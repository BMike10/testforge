from pathlib import Path
from typing import Dict, Any
from testforge.core.context import ModuleInfo

class ArchitectureGenerator:
    """
    Generates a Markdown representation of the codebase architecture.
    """

    @staticmethod
    def to_markdown(arch_map: Dict[str, ModuleInfo]) -> str:
        md = "# Project Architecture & Dependency Map\n\n"
        
        for file_path, info in arch_map.items():
            md += f"## Module: `{file_path}`\n"
            
            if info.imports:
                md += "### Imports\n"
                for imp in info.imports:
                    md += f"- `{imp}`\n"
                md += "\n"
            
            if info.classes:
                md += "### Classes\n"
                for cls in info.classes:
                    md += f"- **{cls.name}**\n"
                    if cls.docstring:
                        md += f"  - *{cls.docstring.strip()}*\n"
                    for method in cls.methods:
                        md += f"  - `method {method.name}({', '.join(method.args)})`\n"
                md += "\n"
            
            if info.functions:
                md += "### Functions\n"
                for func in info.functions:
                    md += f"- `function {func.name}({', '.join(func.args)})`\n"
                    if func.docstring:
                        md += f"  - *{func.docstring.strip()}*\n"
                md += "\n"
            
            md += "---\n\n"
        
        return md

    @staticmethod
    def save_to_file(md_content: str, output_path: Path):
        with open(output_path, "w") as f:
            f.write(md_content)
