import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

class TemplateManager:
    """
    Manages loading and rendering of prompt templates.
    Allows users to override default templates by placing them in `.testforge/templates/`
    within their project root.
    """
    def __init__(self, project_root: Path = Path(".")):
        self.project_root = project_root
        
        # User defined templates path
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
            lstrip_blocks=True
        )

    def render(self, template_name: str, **kwargs) -> str:
        """
        Renders a template with the given context variables.
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
