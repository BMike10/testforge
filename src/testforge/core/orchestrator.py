import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from testforge.core.context import ContextManager
from testforge.agents.coder import CoderAgent
from testforge.core.evaluator import Evaluator
from testforge.utils.env_setup import EnvironmentManager
from testforge.core.state import StateTracker
from rich.console import Console
from rich.panel import Panel
import yaml

console = Console()

class Orchestrator:
    """
    Coordinates the advanced TestForge pipeline:
    Topological Sort -> Environment Setup -> Plan -> Generate -> Pytest -> Mutation Testing.
    """

    def __init__(self, agent: Optional[CoderAgent] = None):
        self.agent = agent or CoderAgent()

    async def run_pipeline_on_project(self, project_root: Path, force: bool = False, dry_run: bool = False, verbose: bool = False):
        """
        Runs the full iterative pipeline on the entire project in topological order.
        """
        tracker = StateTracker(project_root)
        if force:
            tracker.clear()

        # 1. Environment Setup
        if not dry_run:
            EnvironmentManager.setup_testing_env(project_root)

        plan_file = project_root / "execution_plan.yaml"
        plan_data = None

        if not dry_run and plan_file.exists() and not force:
            console.print(f"[green]Found existing execution_plan.yaml, loading plan...[/green]")
            with open(plan_file, "r") as f:
                plan_data = yaml.safe_load(f)
            order = plan_data.get("execution_order", [])
            skipped = []
        else:
            # 2. Build Dependency Graph
            console.print("[blue]Building dependency graph...[/blue]")
            graph = ContextManager.build_dependency_graph(project_root)
            full_order = ContextManager.get_topological_sort(graph)

            order = []
            skipped = []
            for mod in full_order:
                info = graph.nodes[mod].get("info")
                if info and getattr(info, "is_testable", True):
                    order.append(mod)
                else:
                    skipped.append(mod)

            console.print(f"[green]Found {len(full_order)} modules. Processing {len(order)} testable modules ({len(skipped)} skipped based on heuristics).[/green]")

            if skipped:
                console.print(f"[dim]Skipped modules: {', '.join(skipped)}[/dim]")

            # Generate the execution plan details
            plan_data = {"execution_order": order, "phases": {}}
            for i, mod in enumerate(order, 1):
                deps = list(graph.predecessors(mod))
                context_files = [mod] + deps
                plan_data["phases"][f"Phase_{i}"] = {
                    "module": mod,
                    "context_files": context_files,
                    "expected_output": f"tests/test_{Path(mod).stem}.py"
                }

            if dry_run:
                with open(plan_file, "w") as f:
                    yaml.dump(plan_data, f, default_flow_style=False, sort_keys=False)
                console.print(f"[green]Generated editable plan file: {plan_file}[/green]")

                from testforge.utils.output import PipelineReport
                PipelineReport.display_dry_run_summary(order, project_root, graph, verbose=verbose)
                return

        # 3. Ensure Architecture Map exists
        arch_map_path = project_root / "architecture.md"
        if not arch_map_path.exists():
            console.print("[yellow]architecture.md not found. Generating a baseline...[/yellow]")
            arch_map = ContextManager.build_architecture_map(project_root)
            from testforge.utils.output import ArchitectureGenerator
            md = ArchitectureGenerator.to_markdown(arch_map)
            ArchitectureGenerator.save_to_file(md, arch_map_path)

        for i, rel_path in enumerate(order, 1):
            abs_path = project_root / rel_path
            str_path = str(rel_path)
            
            custom_context = None
            if plan_data and "phases" in plan_data:
                phase_key = f"Phase_{i}"
                if phase_key in plan_data["phases"]:
                    custom_context = plan_data["phases"][phase_key].get("context_files")

            if tracker.is_completed(str_path):
                console.print(f"[blue]Skipping already validated module: {str_path}[/blue]")
                continue

            console.print(f"\n[bold cyan]>>> Processing Module: {str_path}[/bold cyan]")
            try:
                results = await self.generate_and_validate(abs_path, project_root, arch_map_path, custom_context=custom_context)
                if results and results.get("success"):
                    tracker.mark_completed(str_path)
                else:
                    tracker.mark_failed(str_path, error="Validation failed")
            except Exception as e:
                console.print(f"[red]Error processing module {str_path}: {e}[/red]")
                tracker.mark_failed(str_path, error=str(e))

        from testforge.utils.output import PipelineReport
        PipelineReport.display_status(tracker, len(order))

    async def plan_module_tests(self, file_path: Path, project_root: Optional[Path] = None, arch_map_path: Optional[Path] = None, custom_context: Optional[List[str]] = None) -> str:
        """
        Executes the 'Scientific Planning' phase for a single module.
        """
        root = project_root or file_path.parent
        arch_path = arch_map_path or (root / "architecture.md")
        
        if not arch_path.exists():
            with open(arch_path, "w") as f: f.write("# Architecture\n")

        console.print(f"[blue]Analyzing {file_path.name} deterministically...[/blue]")
        module_info = ContextManager.analyze_file(file_path, root)
        
        interface_summary = [f"{c.name} (complexity: {c.complexity})" for c in module_info.classes]
        interface_summary += [f"function {f.name} (complexity: {f.complexity})" for f in module_info.functions]

        deterministic_context = {
            "total_complexity": module_info.total_complexity,
            "internal_dependencies": list(module_info.internal_dependencies),
            "interface_summary": interface_summary
        }
        
        if custom_context:
            deterministic_context["custom_context_files"] = custom_context

        rel_path = str(file_path.relative_to(root))
        rel_arch_path = str(arch_path.relative_to(root))
        
        plan_path = await self.agent.plan_tests(rel_path, rel_arch_path, deterministic_context)
        return plan_path

    async def generate_and_validate(self, file_path: Path, project_root: Path, arch_map_path: Path, max_retries: int = 3, custom_context: Optional[List[str]] = None):
        """
        Runs the multi-stage pipeline on a single file.
        """
        rel_path = str(file_path.relative_to(project_root))
        self.agent.clear_context()
        
        console.print(f"[yellow]Planning tests for {rel_path}...[/yellow]")
        plan_path = await self.plan_module_tests(file_path, project_root, arch_map_path, custom_context=custom_context)
        
        test_path = f"tests/test_{file_path.stem}.py"
        console.print(f"[yellow]Generating test suite: {test_path}[/yellow]")
        await self.agent.generate_test_suite(rel_path, plan_path, test_path)
        
        abs_test_path = project_root / test_path
        
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

        console.print(f"[blue]Running Mutation Testing for {rel_path}...[/blue]")
        mut_results = Evaluator.run_mutation_testing(file_path, abs_test_path)
        
        return {"success": True, "test_file": test_path}
