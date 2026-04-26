import typer
import asyncio
from rich.console import Console
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from testforge.agents.coder import CoderAgent
from testforge.core.context import ContextManager
from testforge.utils.output import ArchitectureGenerator
from testforge.core.orchestrator import Orchestrator

# Load environment variables from .env
load_dotenv()

app = typer.Typer(
    help="TestForge: Scientifically Validated AI Test Generation",
    rich_markup_mode="rich"
)
console = Console()

from testforge.core.tokens import TokenEstimator

@app.command()
def map(
    path: Path = typer.Argument(..., help="Path to the codebase to analyze"),
    output: Optional[Path] = typer.Option("architecture.md", help="Output file for the architecture map"),
    mapper_model: Optional[str] = typer.Option(None, help="LLM model for the mapping phase"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate tokens and cost without running AI")
):
    """
    [bold blue]Map[/bold blue] the architecture and dependencies of a codebase.
    """
    console.print(f"[green]Mapping architecture for:[/green] {path}")
    
    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist.[/red]")
        raise typer.Exit(code=1)

    arch_map = ContextManager.build_architecture_map(path)
    deterministic_md = ArchitectureGenerator.to_markdown(arch_map)
    
    if dry_run:
        tokens = TokenEstimator.estimate_string_tokens(deterministic_md)
        TokenEstimator.print_cost_estimate(tokens, "Mapping Phase")
        return
        
    console.print("[yellow]Generating AI semantic summary...[/yellow]")
    agent = CoderAgent(mapper_model=mapper_model)
    semantic_summary = asyncio.run(agent.summarize_architecture(deterministic_md))
    
    full_md = f"{deterministic_md}\n\n# AI Semantic Summary\n\n{semantic_summary}"
    ArchitectureGenerator.save_to_file(full_md, output)
    
    console.print(f"[yellow]Architecture map saved to {output}[/yellow]")

@app.command()
def plan(
    file_path: Path = typer.Argument(..., help="The specific file to plan tests for"),
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    planner_model: Optional[str] = typer.Option(None, help="LLM model for the planning phase"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate tokens and cost without running AI")
):
    """
    [bold magenta]Plan[/bold magenta] a testing strategy for a specific module.
    """
    console.print(f"[green]Planning tests for:[/green] {file_path}")
    
    if dry_run:
        arch_map_path = project_root.absolute() / "architecture.md"
        tokens_target = TokenEstimator.estimate_file_tokens(file_path.absolute())
        tokens_arch = TokenEstimator.estimate_file_tokens(arch_map_path)
        TokenEstimator.print_cost_estimate(tokens_target + tokens_arch, "Planning Phase")
        return
        
    agent = CoderAgent(planner_model=planner_model)
    orchestrator = Orchestrator(agent=agent)
    plan_file = asyncio.run(orchestrator.plan_module_tests(file_path.absolute(), project_root.absolute()))
    
    console.print(f"\n[bold yellow]Generated Test Plan ({plan_file}):[/bold yellow]")
    
    # Read and print the plan content
    plan_abs_path = project_root.absolute() / plan_file
    if plan_abs_path.exists():
        with open(plan_abs_path, "r") as f:
            console.print(f.read())
    else:
        console.print(f"[red]Error: Plan file {plan_abs_path} not found.[/red]")

@app.command()
def generate(
    file_path: Path = typer.Argument(..., help="The file to generate tests for"),
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    planner_model: Optional[str] = typer.Option(None, help="LLM model for the planning phase"),
    coder_model: Optional[str] = typer.Option(None, help="LLM model for the coding phase"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Estimate tokens and cost without running AI")
):
    """
    [bold cyan]Generate[/bold cyan] and validate a unit test suite using the AI-Judge loop.
    """
    console.print(f"[green]Generating tests for:[/green] {file_path}")
    
    if dry_run:
        plan_file = project_root.absolute() / f"test_plan_{file_path.stem}.md"
        tokens_target = TokenEstimator.estimate_file_tokens(file_path.absolute())
        tokens_plan = TokenEstimator.estimate_file_tokens(plan_file)
        TokenEstimator.print_cost_estimate(tokens_target + tokens_plan, "Generation Phase")
        return
        
    agent = CoderAgent(planner_model=planner_model, coder_model=coder_model)
    orchestrator = Orchestrator(agent=agent)
    # Ensure architecture.md exists or generate it
    arch_map_path = project_root.absolute() / "architecture.md"
    
    results = asyncio.run(orchestrator.generate_and_validate(
        file_path.absolute(), 
        project_root.absolute(), 
        arch_map_path
    ))
    
    if results and results.get("success"):
        console.print("[bold green]Success![/bold green] Tests passed and validated.")
    else:
        console.print("[bold red]Fail.[/bold red] Tests did not pass validation.")
        if results:
            console.print(results.get("stdout", ""))
            console.print(results.get("stderr", ""))

@app.command()
def run_all(
    path: Path = typer.Argument(Path("."), help="Project root directory"),
    mapper_model: Optional[str] = typer.Option(None, help="LLM model for the mapping phase"),
    planner_model: Optional[str] = typer.Option(None, help="LLM model for the planning phase"),
    coder_model: Optional[str] = typer.Option(None, help="LLM model for the coding phase"),
    force: bool = typer.Option(False, "--force", help="Force run by clearing the execution ledger"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Output topological order without running")
):
    """
    [bold green]Run All[/bold green]: Execute the full iterative pipeline (Bottom-Up) on the entire codebase.
    """
    console.print(f"[bold blue]Starting Full TestForge Pipeline for:[/bold blue] {path.absolute()}")
    
    agent = CoderAgent(mapper_model=mapper_model, planner_model=planner_model, coder_model=coder_model)
    orchestrator = Orchestrator(agent=agent)
    asyncio.run(orchestrator.run_pipeline_on_project(path.absolute(), force=force, dry_run=dry_run))

@app.command()
def ci(
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    base_branch: str = typer.Option("main", help="Base branch to diff against"),
    mapper_model: Optional[str] = typer.Option(None, help="LLM model for the mapping phase"),
    planner_model: Optional[str] = typer.Option(None, help="LLM model for the planning phase"),
    coder_model: Optional[str] = typer.Option(None, help="LLM model for the coding phase"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Output topological order without running")
):
    """
    [bold yellow]CI/CD Headless Mode[/bold yellow]: Generate tests only for modified files and their dependents.
    """
    console.print(f"[bold blue]Starting CI Pipeline for:[/bold blue] {project_root.absolute()} against [yellow]{base_branch}[/yellow]")
    
    affected = ContextManager.get_affected_modules(project_root.absolute(), base_branch)
    if not affected:
        console.print("[green]No changed Python files or downstream dependents found. Exiting.[/green]")
        return
        
    console.print(f"[yellow]Affected modules ({len(affected)}):[/yellow]")
    for mod in affected:
        console.print(f" - {mod}")
        
    if dry_run:
        return
        
    agent = CoderAgent(mapper_model=mapper_model, planner_model=planner_model, coder_model=coder_model)
    orchestrator = Orchestrator(agent=agent)
    
    # We shouldn't use run_pipeline_on_project because we only want specific files.
    # So we'll orchestrate them manually here.
    EnvironmentManager.setup_testing_env(project_root.absolute())
    
    arch_map_path = project_root.absolute() / "architecture.md"
    if not arch_map_path.exists():
        console.print("[yellow]architecture.md not found. Generating a baseline...[/yellow]")
        arch_map = ContextManager.build_architecture_map(project_root.absolute())
        from testforge.utils.output import ArchitectureGenerator
        md = ArchitectureGenerator.to_markdown(arch_map)
        ArchitectureGenerator.save_to_file(md, arch_map_path)
        
    import asyncio
    for rel_path in affected:
        abs_path = project_root.absolute() / rel_path
        console.print(f"\n[bold cyan]>>> Processing Module: {rel_path}[/bold cyan]")
        try:
            asyncio.run(orchestrator.generate_and_validate(abs_path, project_root.absolute(), arch_map_path))
        except Exception as e:
            console.print(f"[red]Error processing {rel_path}: {e}[/red]")

@app.command()
def refactor_fixtures(
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    coder_model: Optional[str] = typer.Option(None, help="LLM model for the refactoring phase")
):
    """
    [bold magenta]Refactor Fixtures[/bold magenta]: Scan test files and elevate local fixtures to conftest.py.
    """
    console.print(f"[bold blue]Refactoring fixtures in:[/bold blue] {project_root.absolute()}")
    
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        console.print("[red]tests/ directory not found.[/red]")
        return
        
    test_files = list(tests_dir.rglob("test_*.py"))
    if not test_files:
        console.print("[yellow]No test files found to refactor.[/yellow]")
        return
        
    conftest_path = tests_dir / "conftest.py"
    if not conftest_path.exists():
        conftest_path.touch()
        
    files_to_refactor = [str(f.absolute()) for f in test_files] + [str(conftest_path.absolute())]
    
    console.print("[yellow]Using AI to aggregate local fixtures into conftest.py...[/yellow]")
    agent = CoderAgent(coder_model=coder_model)
    
    # We will ask aider to do it in one shot, as we give it all test files and conftest.py
    import asyncio
    
    # Just setting up the coder manually
    agent._initialize_coder(files_to_refactor, target_model=agent.coder_model_name)
    prompt = (
        "Scan the provided test files for local `@pytest.fixture` definitions. "
        "If you find duplicate or highly similar local fixtures across multiple files, "
        "extract them, generalize them if necessary, and move them to `tests/conftest.py`. "
        "Then, update the original test files to remove the local fixture definitions "
        "and ensure they rely on the global ones. Ensure the tests still pass."
    )
    agent.coder.run(prompt)
    console.print("[bold green]Fixture refactoring complete.[/bold green]")

if __name__ == "__main__":
    app()
