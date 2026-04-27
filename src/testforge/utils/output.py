from pathlib import Path
from typing import Dict, Any, List
from testforge.core.context import ModuleInfo
from testforge.core.state import StateTracker
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.progress import Progress, BarColumn, TextColumn

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

        # Summary Table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")
        table.add_row("Total modules", f"[bold]{total_testable}[/bold]")
        table.add_row("Validated", f"[bold green]{validated}[/bold green]")
        table.add_row("Failed", f"[bold red]{failed}[/bold red]")
        table.add_row("Not started", f"[bold yellow]{not_started}[/bold yellow]")

        # Milestones
        milestones_table = Table(show_header=False, box=None, padding=(0, 2))
        milestones_table.add_column("Milestone", style="cyan")
        milestones_table.add_column("Status", justify="center")
        milestones_table.add_row("M1 Core >= 80%", m1_status)
        milestones_table.add_row("M2 P0 >= 90%", m2_status)
        milestones_table.add_row("M3 Suite stable", m3_status)

        console.print("\n")
        console.print(Panel(
            Columns([table, milestones_table]),
            title="[bold blue]TestForge Pipeline Post-Mortem[/bold blue]",
            subtitle=f"[bold white]{percent_done:.1f}% Complete[/bold white]",
            expand=False
        ))

        # Progress Bar
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[green]Overall Progress", total=total_testable)
            progress.update(task, completed=validated)

        # Failure Report
        if failed > 0:
            fail_table = Table(title="[bold red]Retry Required: Failed Modules[/bold red]", show_header=True, header_style="bold red")
            fail_table.add_column("Module Path", style="cyan")
            fail_table.add_column("Last Error", style="dim")
            
            modules = tracker.state.get("modules", {})
            for path, info in modules.items():
                if info.get("status") == "failed":
                    error_msg = info.get("error", "Unknown Error")
                    # Truncate long errors
                    if len(error_msg) > 60: error_msg = error_msg[:57] + "..."
                    fail_table.add_row(path, error_msg)
            
            console.print(fail_table)
        
        console.print("\n")

    @staticmethod
    def display_dry_run_summary(order: List[str], project_root: Path, graph: Any, verbose: bool = False):
        """
        Displays a holistic risk and workload summary for the dry-run.
        """
        from testforge.core.tokens import TokenEstimator
        from testforge.core.context import ContextManager
        console = Console()
        
        total_tokens = 0
        total_complexity = 0
        total_classes = 0
        total_functions = 0
        module_metrics = []
        
        for mod in order:
            abs_path = project_root / mod
            deps = list(graph.predecessors(mod))
            context_files = [mod] + deps
            tokens = sum(TokenEstimator.estimate_file_tokens(project_root / f) for f in context_files)
            total_tokens += tokens
            
            # Analyze for complexity
            try:
                mod_info = ContextManager.analyze_file(abs_path, project_root)
                complexity = mod_info.total_complexity
                classes = len(mod_info.classes)
                functions = len(mod_info.functions)
            except Exception:
                complexity = 0
                classes = 0
                functions = 0
            
            total_complexity += complexity
            total_classes += classes
            total_functions += functions
            
            module_metrics.append({
                "path": mod,
                "tokens": tokens,
                "complexity": complexity,
                "num_files": len(context_files),
                "context_files": context_files,
                "classes": classes,
                "functions": functions
            })

        # 1. High Level Workload
        cost = (total_tokens / 1000000) * 5.00 # $5 per 1M tokens
        workload_panel = Panel(
            f"[bold]Total Modules:[/bold] {len(order)}\n"
            f"[bold]Total Symbols:[/bold] {total_classes} Classes, {total_functions} Functions\n"
            f"[bold]Total Project Complexity:[/bold] {total_complexity}\n"
            f"[bold]Estimated Tokens:[/bold] {total_tokens:,}\n"
            f"[bold]Estimated Cost:[/bold] [green]${cost:.2f}[/green] [dim](GPT-4o rates)[/dim]",
            title="[bold yellow]Project Workload Analysis[/bold yellow]",
            expand=False
        )

        console.print("\n")
        console.print(workload_panel)

        if verbose:
            # 2. Detailed Audit Table
            audit_table = Table(title="[bold cyan]Full Pipeline Audit[/bold cyan]", show_header=True, header_style="bold cyan")
            audit_table.add_column("Phase", justify="center")
            audit_table.add_column("Module", style="white")
            audit_table.add_column("Complexity", justify="right")
            audit_table.add_column("Tokens", justify="right")
            audit_table.add_column("Context Files", style="dim")

            for i, item in enumerate(module_metrics, 1):
                ctx_files = "\n".join([f"• {f}" for f in item["context_files"]])
                audit_table.add_row(
                    str(i),
                    item["path"],
                    f"{item['complexity']}",
                    f"{item['tokens']:,}",
                    ctx_files
                )
            console.print(audit_table)
        else:
            # 2. Risk Profile Table (Concise)
            risk_table = Table(title="[bold red]McCabe Risk Profile: Top Battlefronts[/bold red]", show_header=True, header_style="bold magenta")
            risk_table.add_column("Module", style="cyan")
            risk_table.add_column("Complexity", justify="right")
            risk_table.add_column("Context Bloat", justify="right")
            
            # Sort by complexity
            top_complexity = sorted(module_metrics, key=lambda x: x['complexity'], reverse=True)[:5]
            for item in top_complexity:
                risk_table.add_row(
                    item["path"], 
                    f"[bold]{item['complexity']}[/bold]", 
                    f"{item['tokens']:,} tokens ({item['num_files']} files)"
                )
            console.print(risk_table)

        console.print("\n[dim]Tip: Edit 'execution_plan.yaml' to refine context and optimize costs before running.[/dim]\n")
