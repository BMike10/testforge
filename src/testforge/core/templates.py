import os
import warnings
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined, meta

class TemplateManager:
    """
    Manages loading and rendering of prompt templates with strict validation.
    Allows users to override default templates by placing them in `.testforge/templates/`
    within their project root.
    """
    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        
        # User defined templates path - Priority 1: Env Var, Priority 2: .testforge/templates
        env_templates_dir = os.environ.get("TESTFORGE_TEMPLATES_DIR")
        if env_templates_dir:
            self.user_templates_dir = Path(env_templates_dir)
        else:
            self.user_templates_dir = self.project_root / ".testforge" / "templates"
        
        # Default package templates path
        self.default_templates_dir = Path(__file__).parent.parent / "templates"
        
        # Set up Jinja2 environment to look in user dir first, then default dir
        search_paths = []
        if self.user_templates_dir.exists():
            search_paths.append(str(self.user_templates_dir))
        search_paths.append(str(self.default_templates_dir))
        
        self.env = Environment(
            loader=FileSystemLoader(search_paths),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined
        )

    def _get_undeclared_variables(self, template_name: str) -> set[str]:
        """
        Extracts all variables used in the template via AST analysis.
        """
        template_source = self.env.loader.get_source(self.env, template_name)[0]
        parsed_content = self.env.parse(template_source)
        return meta.find_undeclared_variables(parsed_content)

    def render(self, template_name: str, **kwargs) -> str:
        """
        Renders a template with the given context variables and validates them.
        """
        # Validate variables against template AST
        try:
            required_vars = self._get_undeclared_variables(template_name)
            provided_vars = set(kwargs.keys())
            
            # Check for extra (unused) variables to detect code/template drift
            unused_vars = provided_vars - required_vars
            if unused_vars:
                warnings.warn(
                    f"Template '{template_name}' does not use variables: {unused_vars}. "
                    "This might indicate drift between the code and the template.",
                    UserWarning
                )
        except Exception as e:
            # Fallback for complex templates where AST parsing might fail
            # We don't want to break the pipeline if AST analysis is too complex
            pass

        template = self.env.get_template(template_name)
        return template.render(**kwargs)
