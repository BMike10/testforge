import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from testforge.core.context import ContextManager
from testforge.agents.coder import CoderAgent
from testforge.core.evaluator import Evaluator
from testforge.utils.env_setup import EnvironmentManager
from testforge.core.state import StateTracker
from rich.console import Console

console = Console()

class Orchestrator:
    """
    Coordinates the advanced TestForge pipeline: 
    Topological Sort -> Environment Setup -> Plan -> Generate -> Pytest -> Mutation Testing.
    """

    def __init__(self, agent: Optional[CoderAgent] = None):
        self.agent = agent or CoderAgent()

    async def run_pipeline_on_project(self, project_root: Path, force: bool = False, dry_run: bool = False):
        """
        Runs the full iterative pipeline on the entire project in topological order.
        """
        tracker = StateTracker(project_root)
        if force:
            tracker.clear()
            
        # 1. Environment Setup
        if not dry_run:
            EnvironmentManager.setup_testing_env(project_root)
        
        # 2. Build Dependency Graph
        console.print("[blue]Building dependency graph...[/blue]")
        graph = ContextManager.build_dependency_graph(project_root)
        order = ContextManager.get_topological_sort(graph)
        
        console.print(f"[green]Processing {len(order)} modules in bottom-up order.[/green]")
        
        if dry_run:
            console.print("[yellow]Dry-run enabled: Outputting topological order only.[/yellow]")
            for mod in order:
                console.print(f" - {mod}")
            return
            
        # 3. Ensure Architecture Map exists
        arch_map_path = project_root / "architecture.md"
        if not arch_map_path.exists():
            console.print("[yellow]architecture.md not found. Generating a baseline...[/yellow]")
            # In a real run, the user should probably run 'map' first, 
            # but we can trigger it here.
            arch_map = ContextManager.build_architecture_map(project_root)
            from testforge.utils.output import ArchitectureGenerator
            md = ArchitectureGenerator.to_markdown(arch_map)
            ArchitectureGenerator.save_to_file(md, arch_map_path)
        
        for rel_path in order:
            abs_path = project_root / rel_path
            str_path = str(rel_path)
            
            if tracker.is_completed(str_path):
                console.print(f"[blue]Skipping already validated module: {str_path}[/blue]")
                continue
                
            console.print(f"\n[bold cyan]>>> Processing Module: {str_path}[/bold cyan]")
            try:
                results = await self.generate_and_validate(abs_path, project_root, arch_map_path)
                if results and results.get("success"):
                    tracker.mark_completed(str_path)
                else:
                    tracker.mark_failed(str_path, error="Validation failed")
            except Exception as e:
                console.print(f"[red]Error processing module {str_path}: {e}[/red]")
                tracker.mark_failed(str_path, error=str(e))

    async def plan_module_tests(self, file_path: Path, project_root: Optional[Path] = None, arch_map_path: Optional[Path] = None) -> str:
        """
        Executes the 'Scientific Planning' phase for a single module.
        """
        root = project_root or file_path.parent
        arch_path = arch_map_path or (root / "architecture.md")
        
        if not arch_path.exists():
            # Create a dummy or baseline if missing
            with open(arch_path, "w") as f: f.write("# Architecture\n")

        # 1. Deterministic Analysis for Planning
        console.print(f"[blue]Analyzing {file_path.name} deterministically...[/blue]")
        module_info = ContextManager.analyze_file(file_path, root)
        
        interface_summary = [f"{c.name} (complexity: {c.complexity})" for c in module_info.classes]
        interface_summary += [f"function {f.name} (complexity: {f.complexity})" for f in module_info.functions]

        deterministic_context = {
            "total_complexity": module_info.total_complexity,
            "internal_dependencies": list(module_info.internal_dependencies),
            "interface_summary": interface_summary
        }

        # 2. AI-Driven Planning
        rel_path = str(file_path.relative_to(root))
        rel_arch_path = str(arch_path.relative_to(root))
        
        plan_path = await self.agent.plan_tests(rel_path, rel_arch_path, deterministic_context)
        return plan_path

    async def generate_and_validate(self, file_path: Path, project_root: Path, arch_map_path: Path, max_retries: int = 3):
        """
        Runs the multi-stage pipeline on a single file.
        """
        rel_path = str(file_path.relative_to(project_root))
        
        # 1. Clear Agent Context for strict isolation
        self.agent.clear_context()
        
        # 2. Planning Phase
        console.print(f"[yellow]Planning tests for {rel_path}...[/yellow]")
        plan_path = await self.plan_module_tests(file_path, project_root, arch_map_path)
        
        # 3. Generation Phase
        test_path = f"tests/test_{file_path.stem}.py"
        console.print(f"[yellow]Generating test suite: {test_path}[/yellow]")
        await self.agent.generate_test_suite(rel_path, plan_path, test_path)
        
        abs_test_path = project_root / test_path
        
        # 4. AI-Judge Loop (Pytest)
        for attempt in range(max_retries + 1):
            results = Evaluator.run_pytest(abs_test_path)
            if results["success"]:
                console.print(f"[green]✔ Tests passed for {rel_path}[/green]")
                break
            
            if attempt < max_retries:
                console.print(f"[red]✘ Tests failed (Attempt {attempt + 1}). Repairing...[/red]")
                error_output = results.get("stdout", "") + results.get("stderr", "")
                await self.agent.repair_test_suite(test_path, error_output)
            else:
                console.print(f"[bold red]✘ Max retries reached for {rel_path}.[/bold red]")
                return results

        # 5. Scientific Validation (Mutation Testing)
        console.print(f"[blue]Running Mutation Testing for {rel_path}...[/blue]")
        mut_results = Evaluator.run_mutation_testing(file_path, abs_test_path)
        
        return {"success": True, "test_file": test_path}
