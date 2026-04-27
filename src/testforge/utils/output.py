from pathlib import Path
from typing import Dict, Any
from testforge.core.context import ModuleInfo
from testforge.core.state import StateTracker
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

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

class PipelineReport:
    """
    Generates a visual dashboard for the pipeline execution state.
    """
    @staticmethod
    def display_status(tracker: StateTracker, total_testable: int):
        console = Console()
        stats = tracker.get_stats()
        validated = stats["validated"]
        failed = stats["failed"]
        not_started = max(0, total_testable - validated - failed)
        
        percent_done = (validated / total_testable * 100) if total_testable > 0 else 0
        
        m1_status = "✅" if percent_done >= 80 else "⏳"
        m2_status = "✅" if percent_done >= 90 else "⏳"
        m3_status = "✅" if percent_done == 100 and failed == 0 else "⏳"

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        table.add_row("Total modules", str(total_testable))
        table.add_row("Validated", f"[green]{validated}[/green]")
        table.add_row("Failed", f"[red]{failed}[/red]")
        table.add_row("Not started", f"[yellow]{not_started}[/yellow]")

        milestones_table = Table(show_header=False, box=None)
        milestones_table.add_column("Milestone", style="cyan")
        milestones_table.add_column("Status", justify="center")
        
        milestones_table.add_row("M1 Core >= 80%", m1_status)
        milestones_table.add_row("M2 P0 >= 90%", m2_status)
        milestones_table.add_row("M3 Suite stable", m3_status)

        console.print("\n")
        console.print(Columns([
            Panel(table, title="[bold]Pipeline Status[/bold]", expand=True),
            Panel(milestones_table, title="[bold]Milestones[/bold]", expand=True)
        ]))
        console.print("\n")
