import os
from typing import List, Optional
from aider.coders import Coder
from aider.models import Model
from aider.io import InputOutput
from pathlib import Path
from testforge.core.templates import TemplateManager

class CoderAgent:
    """
    Agent responsible for generating code and test plans using Aider.
    Leverages Aider's Python API for advanced context management and file editing.
    """

    def __init__(self, mapper_model: Optional[str] = None, planner_model: Optional[str] = None, coder_model: Optional[str] = None):
        default_model = os.getenv("LLM_MODEL_NAME", "gpt-4o")
        self.mapper_model_name = mapper_model or os.getenv("LLM_MAPPER_MODEL") or default_model
        self.planner_model_name = planner_model or os.getenv("LLM_PLANNER_MODEL") or default_model
        self.coder_model_name = coder_model or os.getenv("LLM_CODER_MODEL") or default_model
        
        self.api_base = os.getenv("LLM_API_BASE")
        self.api_key = os.getenv("LLM_API_KEY")
        
        self._setup_env()

        self.io = InputOutput(yes=True)
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
                # If coder already exists, we might need to recreate it or update its main_model
                # To be safe and clean, we recreate it when switching models if context is not needed,
                # but Aider's Coder allows setting main_model directly.
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
                auto_commits=False
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

    async def summarize_architecture(self, architecture_map: str) -> str:
        """
        Uses AI to generate a high-level semantic summary of the architecture map.
        """
        # Aider works best with files in context. 
        # We'll create a temporary file for the architecture map to give Aider context.
        temp_arch_file = "temp_architecture_map.txt"
        with open(temp_arch_file, "w") as f:
            f.write(architecture_map)
        
        self._initialize_coder([temp_arch_file], target_model=self.mapper_model_name)
        
        prompt = self.template_manager.render(
            "summarize_architecture.j2",
            temp_arch_file=temp_arch_file
        )
        response = self.coder.run(prompt)
        
        # Cleanup temp file
        if os.path.exists(temp_arch_file):
            os.remove(temp_arch_file)
            
        return response

    async def plan_tests(self, module_path: str, architecture_path: str, deterministic_context: Optional[dict] = None) -> str:
        """
        Instructs Aider to create a test plan for the given module, incorporating deterministic analysis.
        """
        self._initialize_coder([module_path, architecture_path], target_model=self.planner_model_name)
        plan_file = f"test_plan_{Path(module_path).stem}.md"
        
        prompt = self.template_manager.render(
            "plan_tests.j2",
            module_path=module_path,
            deterministic_context=deterministic_context,
            plan_file=plan_file,
            architecture_path=architecture_path
        )
        
        self.coder.run(prompt)
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

    async def repair_test_suite(self, test_path: str, error_output: str):
        """
        Uses Aider to fix failing tests by providing the error output.
        """
        self._initialize_coder([test_path], target_model=self.coder_model_name)
        
        prompt = self.template_manager.render(
            "repair_test_suite.j2",
            test_path=test_path,
            error_output=error_output
        )
        self.coder.run(prompt)
