from testforge.utils.env_setup import EnvironmentManager
import typer
import asyncio
import os
import shutil
import subprocess
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
    dry_run: bool = typer.Option(False, "--dry-run", help="Output topological order without running"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Detailed dry-run output including full context audit")
):
    """
    [bold green]Run All[/bold green]: Execute the full iterative pipeline (Bottom-Up) on the entire codebase.
    """
    console.print(f"[bold blue]Starting Full TestForge Pipeline for:[/bold blue] {path.absolute()}")
    
    agent = CoderAgent(mapper_model=mapper_model, planner_model=planner_model, coder_model=coder_model)
    orchestrator = Orchestrator(agent=agent)
    asyncio.run(orchestrator.run_pipeline_on_project(path.absolute(), force=force, dry_run=dry_run, verbose=verbose))

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

@app.command()
def chat(
    files: Optional[list[Path]] = typer.Argument(None, help="Additional files to include in the chat"),
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    coder_model: Optional[str] = typer.Option(None, help="LLM model for the chat session")
):
    """
    [bold blue]Chat[/bold blue]: Launch an interactive Aider session pre-loaded with TestForge context.
    """
    console.print("[bold blue]Launching interactive Aider session...[/bold blue]")
    
    arch_map_path = project_root.absolute() / "architecture.md"
    if not arch_map_path.exists():
        console.print("[yellow]architecture.md not found. Generating it for context...[/yellow]")
        arch_map = ContextManager.build_architecture_map(project_root.absolute())
        md = ArchitectureGenerator.to_markdown(arch_map)
        ArchitectureGenerator.save_to_file(md, arch_map_path)
    
    # Construct the aider command
    cmd = ["aider"]
    
    # Use specified model or fall back to environment
    model = coder_model or os.getenv("LLM_CODER_MODEL") or os.getenv("LLM_MODEL_NAME")
    if model:
        # We need to format it for aider if it's a custom provider
        # But for the CLI, we'll just pass it as is and let aider handle it or the user provide the correct name
        cmd.extend(["--model", model])
    
    # Add architecture.md as read-only context
    cmd.extend(["--read", str(arch_map_path)])
    
    # Add any additional files
    if files:
        for f in files:
            cmd.append(str(f.absolute()))
            
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        console.print("[red]Error: 'aider' CLI not found. Please install it with 'pip install aider-chat'.[/red]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Aider session exited with an error: {e}[/red]")

from testforge.core.templates import TemplateManager

@app.command()
def init_templates(
    project_root: Path = typer.Option(Path("."), help="Project root directory"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing templates")
):
    """
    [bold yellow]Initialize Templates[/bold yellow]: Copy default Jinja2 templates to the user's workspace for customization.
    """
    manager = TemplateManager(project_root=project_root)
    target_dir = manager.user_templates_dir
    source_dir = manager.default_templates_dir
    
    if not source_dir.exists():
        console.print(f"[red]Error: Default templates directory not found at {source_dir}[/red]")
        raise typer.Exit(code=1)
        
    console.print(f"[blue]Target directory:[/blue] {target_dir}")
    
    if target_dir.exists() and not force:
        console.print("[yellow]Templates directory already exists. Use --force to overwrite.[/yellow]")
        return
        
    if not target_dir.exists():
        target_dir.mkdir(parents=True)
        
    # Copy all .j2 files
    templates = list(source_dir.glob("*.j2"))
    if not templates:
        console.print(f"[yellow]No templates found in {source_dir}[/yellow]")
        return
        
    for template in templates:
        dest = target_dir / template.name
        shutil.copy2(template, dest)
        console.print(f" - [green]Copied:[/green] {template.name}")
        
    console.print("\n[bold green]Success![/bold green] You can now customize your templates in the target directory.")
    console.print("TestForge will prioritize these templates over the package defaults.")

if __name__ == "__main__":
    app()
