import os
import io
import re
import litellm
from typing import List, Optional
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from pathlib import Path
from testforge.core.templates import TemplateManager

class CoderAgent:
    """
    Agent responsible for generating code and test plans using Aider or direct LLM calls.
    Leverages Aider for file editing and direct LiteLLM for lightweight analysis.
    """

    def __init__(self, mapper_model: Optional[str] = None, planner_model: Optional[str] = None, coder_model: Optional[str] = None):
        default_model = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.mapper_model_name = mapper_model or os.getenv("LLM_MAPPER_MODEL") or default_model
        self.planner_model_name = planner_model or os.getenv("LLM_PLANNER_MODEL") or default_model
        self.coder_model_name = coder_model or os.getenv("LLM_CODER_MODEL") or default_model
        
        self.api_base = os.getenv("LLM_API_BASE")
        self.api_key = os.getenv("LLM_API_KEY")
        
        self._setup_env()

        # Initialize Aider in silent mode to prevent I/O pollution for editing tasks
        self.silent_stream = open(os.devnull, 'w')
        self.io = InputOutput(
            yes=True, 
            pretty=False, 
            fancy_input=False,
            output=self.silent_stream
        )
        # Manually override Aider's internal console to ensure it respects our silent stream
        from rich.console import Console
        self.io.console = Console(file=self.silent_stream, force_terminal=False, no_color=True)
        
        self.coder: Optional[Coder] = None
        self.template_manager = TemplateManager()
        
        # We start with mapper model by default, but we'll dynamically switch
        self.current_model_name = self.mapper_model_name
        self.main_model = Model(self._format_model_name(self.current_model_name))

    def _format_model_name(self, model_name: str) -> str:
        if self.api_base and "/" in model_name and not model_name.startswith(("openai/", "anthropic/", "gemini/", "openrouter/")):
            if "127.0.0.1" in self.api_base or "localhost" in self.api_base:
                return f"openai/{model_name}"
        return model_name

    def _setup_env(self):
        if self.api_base:
            os.environ["OPENAI_API_BASE"] = self.api_base

        if self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key
        elif not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = "no-key"

    def _switch_model(self, target_model_name: str):
        """Switches the active model if different from the current one."""
        if self.current_model_name != target_model_name:
            self.current_model_name = target_model_name
            self.main_model = Model(self._format_model_name(self.current_model_name))
            if self.coder:
                self.coder.main_model = self.main_model

    def _initialize_coder(self, fnames: List[str], target_model: Optional[str] = None):
        """
        Initializes or updates the Aider coder with a specific set of files.
        Optionally switches the model before initializing.
        """
        if target_model:
            self._switch_model(target_model)

        if self.coder:
            # Update existing coder's files
            for fname in fnames:
                if fname not in self.coder.abs_fnames:
                    self.coder.add_rel_fname(fname)
        else:
            self.coder = Coder.create(
                main_model=self.main_model,
                io=self.io,
                fnames=fnames,
                auto_commits=False,
                map_tokens=0,
                stream=False
            )

    def add_context(self, file_paths: List[str]):
        """
        Adds files to the Aider context.
        """
        self._initialize_coder(file_paths)

    def clear_context(self):
        """
        Resets the Aider coder to clear context.
        """
        self.coder = None

    def _sanitize_response(self, text: str) -> str:
        """
        Cleans the LLM response of internal UI markers and conversational drift.
        """
        # Remove Aider/Model specific markers
        text = re.sub(r'► (THINKING|ANSWER)', '', text)
        text = re.sub(r'┏━+┓|┗━+┛|┃', '', text)
        
        # Extract reasoning content if present (common in some models)
        # This is a bit tricky, but let's try to find the actual content
        # Most models will put the final answer after the reasoning.
        
        # If the model wrapped the response in markdown blocks, extract only the content
        md_match = re.search(r'```markdown\n(.*?)\n```', text, re.DOTALL)
        if md_match:
            return md_match.group(1).strip()
            
        return text.strip()

    async def _direct_inference(self, prompt: str, model_name: str) -> str:
        """
        Executes a direct completion call bypassing Aider's heavy system prompts.
        Ideal for summarization and planning tasks.
        """
        messages = [{"role": "user", "content": prompt}]
        
        formatted_model = self._format_model_name(model_name)
        
        response = litellm.completion(
            model=formatted_model,
            messages=messages,
            api_base=self.api_base,
            api_key=self.api_key
        )
        
        return response.choices[0].message.content

    async def summarize_architecture(self, architecture_map: str) -> str:
        """
        Uses AI to generate a high-level semantic summary of the architecture map.
        Uses direct inference to prevent conversational drift in small models.
        """
        prompt = self.template_manager.render(
            "summarize_architecture.j2",
            architecture_map=architecture_map
        )
        
        response = await self._direct_inference(prompt, self.mapper_model_name)
        return self._sanitize_response(response)

    async def plan_tests(self, module_path: str, architecture_path: str, deterministic_context: Optional[dict] = None) -> str:
        """
        Instructs the LLM to create a test plan for the given module.
        Uses direct inference to bypass Aider's system prompt.
        """
        # Read files for injection
        with open(module_path, "r") as f:
            module_code = f.read()
        
        with open(architecture_path, "r") as f:
            architecture_map = f.read()

        plan_file = f"test_plan_{Path(module_path).stem}.md"
        
        prompt = self.template_manager.render(
            "plan_tests.j2",
            module_path=module_path,
            module_code=module_code,
            architecture_map=architecture_map,
            deterministic_context=deterministic_context,
            plan_file=plan_file
        )
        
        response = await self._direct_inference(prompt, self.planner_model_name)
        sanitized_plan = self._sanitize_response(response)
        
        # Write the plan to disk (current working directory/root)
        with open(plan_file, "w") as f:
            f.write(sanitized_plan)
            
        return plan_file

    async def generate_test_suite(self, module_path: str, plan_path: str, test_path: str):
        """
        Instructs Aider to generate a pytest suite based on the plan.
        """
        self._initialize_coder([module_path, plan_path], target_model=self.coder_model_name)
        
        prompt = self.template_manager.render(
            "generate_test_suite.j2",
            plan_path=plan_path,
            module_path=module_path,
            test_path=test_path
        )
        self.coder.run(prompt)

    async def repair_test_suite(self, test_path: str, error_output: str, module_path: Optional[str] = None, plan_path: Optional[str] = None, architecture_path: Optional[str] = None):
        """
        Uses Aider to fix failing tests by providing the error output and enriched context.
        """
        fnames = [test_path]
        if module_path: fnames.append(module_path)
        if plan_path: fnames.append(plan_path)
        if architecture_path: fnames.append(architecture_path)

        self._initialize_coder(fnames, target_model=self.coder_model_name)
        
        prompt = self.template_manager.render(
            "repair_test_suite.j2",
            test_path=test_path,
            error_output=error_output
        )
        self.coder.run(prompt)
