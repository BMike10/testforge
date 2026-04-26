# Project Architecture & Dependency Map

## Module: `cli.py`
### Imports
- `typer`
- `asyncio`
- `rich.console.Console`
- `typing.Optional`
- `pathlib.Path`
- `dotenv.load_dotenv`
- `testforge.agents.coder.CoderAgent`
- `testforge.core.context.ContextManager`
- `testforge.utils.output.ArchitectureGenerator`
- `testforge.core.orchestrator.Orchestrator`
- `testforge.core.tokens.TokenEstimator`

### Functions
- `function map(path, output, mapper_model, dry_run)`
  - *[bold blue]Map[/bold blue] the architecture and dependencies of a codebase.*
- `function plan(file_path, project_root, planner_model, dry_run)`
  - *[bold magenta]Plan[/bold magenta] a testing strategy for a specific module.*
- `function generate(file_path, project_root, planner_model, coder_model, dry_run)`
  - *[bold cyan]Generate[/bold cyan] and validate a unit test suite using the AI-Judge loop.*
- `function run_all(path, mapper_model, planner_model, coder_model, force, dry_run)`
  - *[bold green]Run All[/bold green]: Execute the full iterative pipeline (Bottom-Up) on the entire codebase.*
- `function ci(project_root, base_branch, mapper_model, planner_model, coder_model, dry_run)`
  - *[bold yellow]CI/CD Headless Mode[/bold yellow]: Generate tests only for modified files and their dependents.*
- `function refactor_fixtures(project_root, coder_model)`
  - *[bold magenta]Refactor Fixtures[/bold magenta]: Scan test files and elevate local fixtures to conftest.py.*

---

## Module: `__init__.py`
---

## Module: `utils/output.py`
### Imports
- `pathlib.Path`
- `typing.Dict`
- `testforge.core.context.ModuleInfo`

### Classes
- **ArchitectureGenerator**
  - *Generates a Markdown representation of the codebase architecture.*
  - `method to_markdown(arch_map)`
  - `method save_to_file(md_content, output_path)`

---

## Module: `utils/__init__.py`
---

## Module: `utils/env_setup.py`
### Imports
- `os`
- `subprocess`
- `sys`
- `pathlib.Path`
- `rich.console.Console`

### Classes
- **EnvironmentManager**
  - *Automates the setup and verification of the testing environment.*
  - `method setup_testing_env(project_root)`
  - `method validate_execution()`

---

## Module: `agents/coder.py`
### Imports
- `os`
- `typing.List`
- `aider.coders.Coder`
- `aider.models.Model`
- `aider.io.InputOutput`
- `pathlib.Path`
- `testforge.core.templates.TemplateManager`

### Classes
- **CoderAgent**
  - *Agent responsible for generating code and test plans using Aider.
Leverages Aider's Python API for advanced context management and file editing.*
  - `method __init__(self, mapper_model, planner_model, coder_model)`
  - `method _format_model_name(self, model_name)`
  - `method _setup_env(self)`
  - `method _switch_model(self, target_model_name)`
  - `method _initialize_coder(self, fnames, target_model)`
  - `method add_context(self, file_paths)`
  - `method clear_context(self)`

---

## Module: `agents/__init__.py`
---

## Module: `core/templates.py`
### Imports
- `os`
- `pathlib.Path`
- `jinja2.Environment`

### Classes
- **TemplateManager**
  - *Manages loading and rendering of prompt templates.
Allows users to override default templates by placing them in `.testforge/templates/`
within their project root.*
  - `method __init__(self, project_root)`
  - `method render(self, template_name)`

---

## Module: `core/evaluator.py`
### Imports
- `subprocess`
- `os`
- `pathlib.Path`
- `typing.Dict`

### Classes
- **Evaluator**
  - *The 'Judge' that validates generated tests through execution and mutation testing.*
  - `method run_pytest(test_file)`
  - `method run_mutation_testing(target_file, test_file)`

---

## Module: `core/context.py`
### Imports
- `ast`
- `networkx`
- `git`
- `pathlib.Path`
- `typing.List`
- `pydantic.BaseModel`

### Classes
- **FunctionInfo**
- **ClassInfo**
- **ModuleInfo**
- **ContextManager**
  - *Deterministic tool to analyze Python codebase using AST and NetworkX.
Provides context, complexity analysis, and dependency ordering.*
  - `method get_affected_modules(project_root, base_branch)`
  - `method calculate_complexity(node)`
  - `method analyze_file(file_path, project_root)`
  - `method _extract_function_info(node, source_content)`
  - `method build_dependency_graph(root_dir)`
  - `method get_topological_sort(graph)`
  - `method build_architecture_map(root_dir)`

---

## Module: `core/tokens.py`
### Imports
- `tiktoken`
- `pathlib.Path`
- `rich.console.Console`

### Classes
- **TokenEstimator**
  - `method estimate_file_tokens(file_path, model)`
  - `method estimate_string_tokens(content, model)`
  - `method print_cost_estimate(tokens, phase)`

---

## Module: `core/__init__.py`
---

## Module: `core/orchestrator.py`
### Imports
- `asyncio`
- `pathlib.Path`
- `typing.Optional`
- `testforge.core.context.ContextManager`
- `testforge.agents.coder.CoderAgent`
- `testforge.core.evaluator.Evaluator`
- `testforge.utils.env_setup.EnvironmentManager`
- `testforge.core.state.StateTracker`
- `rich.console.Console`

### Classes
- **Orchestrator**
  - *Coordinates the advanced TestForge pipeline: 
Topological Sort -> Environment Setup -> Plan -> Generate -> Pytest -> Mutation Testing.*
  - `method __init__(self, agent)`

---

## Module: `core/state.py`
### Imports
- `json`
- `pathlib.Path`
- `typing.Dict`

### Classes
- **StateTracker**
  - *Manages the Execution Ledger to track the pipeline state and resume interrupted runs.*
  - `method __init__(self, project_root)`
  - `method _load(self)`
  - `method _save(self)`
  - `method mark_completed(self, module_path)`
  - `method mark_failed(self, module_path, error)`
  - `method is_completed(self, module_path)`
  - `method clear(self)`

---



# AI Semantic Summary

# High‑Level Semantic Summary of TestForge Architecture

TestForge is organised around five core concerns:

1. **CLI** – user entry point that orchestrates the whole pipeline.
2. **Agents** – AI‑powered helpers that generate plans and code.
3. **Core** – deterministic analysis, state tracking, orchestration, and evaluation.
4. **Utils** – small helper utilities for environment setup and output formatting.
5. **Templates** – Jinja2 prompt templates that can be overridden by the user.

Below is a module‑by‑module description of responsibilities and how they fit together.

---

## `cli.py`

*Primary Responsibility:*  
Acts as the command‑line interface, exposing sub‑commands such as `map`, `plan`, `generate`, `run_all`, `ci`, and `refactor_fixtures`. Each command delegates to the appropriate core or agent functionality.

*Role in System:*  
- Serves as the user’s entry point.  
- Parses arguments, loads environment variables (`dotenv`), and constructs the necessary objects (agents, orchestrator).  
- Provides a convenient way to run individual stages of the pipeline or the full iterative loop.

---

## `utils/output.py`

*Primary Responsibility:*  
Provides an **ArchitectureGenerator** that turns an internal architecture map into Markdown and writes it to disk.

*Role in System:*  
- Used by the CLI’s `map` command to produce a human‑readable overview of the codebase.  
- Keeps the output logic separate from analysis logic, enabling reuse across other tools or future extensions.

---

## `utils/env_setup.py`

*Primary Responsibility:*  
Defines **EnvironmentManager** which automates setting up and validating the testing environment (e.g., installing dependencies, ensuring required binaries are available).

*Role in System:*  
- Invoked by the orchestrator before running tests.  
- Guarantees that each module is evaluated in a clean, reproducible environment.

---

## `agents/coder.py`

*Primary Responsibility:*  
Implements **CoderAgent**, an AI agent built on Aider’s Python API. It can:

1. Format model names for consistency.
2. Switch between language models.
3. Initialise the coder with context files.
4. Add or clear context as needed.

*Role in System:*  
- Generates test plans (`plan`) and unit tests (`generate`).  
- Encapsulates all AI‑interaction logic, keeping the core orchestration free of model‑specific details.

---

## `core/templates.py`

*Primary Responsibility:*  
**TemplateManager** loads Jinja2 templates from a default location or an overridden `.testforge/templates/` directory within the project root.

*Role in System:*  
- Supplies prompt text to the AI agents.  
- Allows users to customise prompts without modifying code.

---

## `core/evaluator.py`

*Primary Responsibility:*  
**Evaluator** runs generated tests (`run_pytest`) and performs mutation testing (`run_mutation_testing`) to validate test quality.

*Role in System:*  
- Provides the “Judge” that determines whether a generated test suite is adequate.  
- Integrates with the orchestrator’s pipeline, feeding results back into state tracking.

---

## `core/context.py`

*Primary Responsibility:*  
**ContextManager** performs deterministic static analysis:

- Parses Python files with `ast`.
- Builds a dependency graph using `networkx`.
- Calculates cyclomatic complexity.
- Generates an architecture map and topological ordering of modules.

*Role in System:*  
- Supplies the orchestrator with information about which modules depend on each other, enabling correct execution order.  
- Provides context for AI agents to understand code structure.

---

## `core/tokens.py`

*Primary Responsibility:*  
**TokenEstimator** estimates token usage for a given file or string using `tiktoken`.

*Role in System:*  
- Helps the orchestrator decide which model to use and estimate cost, ensuring efficient API utilisation.

---

## `core/orchestrator.py`

*Primary Responsibility:*  
**Orchestrator** coordinates the entire pipeline:

1. Topological sort of modules.
2. Environment setup via **EnvironmentManager**.
3. Planning (`plan`) and generation (`generate`) through **CoderAgent**.
4. Evaluation with **Evaluator**.
5. State tracking via **StateTracker**.

*Role in System:*  
- The central glue that turns individual components into a coherent workflow.  
- Handles retries, error reporting, and progress persistence.

---

## `core/state.py`

*Primary Responsibility:*  
**StateTracker** persists the execution ledger to disk (JSON). It records which modules have completed successfully or failed, enabling resumable runs.

*Role in System:*  
- Prevents re‑processing of already‑handled modules.  
- Provides a simple checkpointing mechanism for long pipelines.

---

## `core/__init__.py` & `agents/__init__.py`

These are package initialisers; they expose the public API of their respective packages but contain no logic themselves.

---

### Summary

TestForge is a modular system that separates concerns cleanly:

- **CLI** → user interaction.  
- **Agents** → AI‑powered code generation.  
- **Core** → deterministic analysis, orchestration, evaluation, and state persistence.  
- **Utils** → environment setup and output formatting.  
- **Templates** → prompt management.

Each module has a single, well‑defined responsibility, making the system extensible and maintainable.