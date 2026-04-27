# CLI Reference 🛠️

Detailed documentation for the TestForge command-line interface. Each command is designed to be deterministic and transparent.

---

## `testforge map`
Builds the architectural topography of the codebase.

```bash
testforge map [PATH] [OPTIONS]
```

**Arguments**:
- `PATH`: Path to the codebase to analyze.

**Options**:
- `--output PATH`: Output file for the architecture map. (Default: `architecture.md`)
- `--mapper-model TEXT`: LLM model for the mapping phase.
- `--dry-run`: Estimate tokens and cost without running AI.

!!! info "Under the Hood: Mapping Logic"
    1.  **File Discovery**: Scans for all `.py` files, respecting `.gitignore`.
    2.  **AST Analysis**: Extracts classes, functions, and docstrings.
    3.  **Cross-Reference**: Matches internal imports to create the dependency mapping.
    4.  **Markdown Generation**: Formats the `ModuleInfo` objects into a human-readable `architecture.md`.

---

## `testforge run-all`
The full iterative pipeline (Bottom-Up) on the entire codebase.

```bash
testforge run-all [PATH] [OPTIONS]
```

**Arguments**:
- `PATH`: Project root directory.

**Options**:
- `--mapper-model TEXT`: LLM model for the mapping phase.
- `--planner-model TEXT`: LLM model for the planning phase.
- `--coder-model TEXT`: LLM model for the coding phase.
- `--force`: Force run by clearing the execution ledger and ignore `execution_plan.yaml`.
- `--dry-run`: Perform a full simulation and generate an editable execution plan.

!!! info "Under the Hood: The Master Pipeline"
    1.  **Dependency Sort**: Builds the DAG and calculates the topological processing order.
    2.  **Heuristic Filtering**: Skips logic-less modules (0 classes/functions).
    3.  **Execution Plan**: 
        *   If `--dry-run`: Generates `execution_plan.yaml` and displays a detailed token/context report.
        *   If Standard Run: Checks for `execution_plan.yaml`. If found, it uses the **user-modified order and context**.
    4.  **State Management**: Updates `.testforge/ledger.json` after every module to enable "Pause and Resume" capability.
    5.  **Scientific Loop**: For each module: `Plan -> Generate -> Pytest -> Mutmut Hardening`.
    6.  **Reporting**: Displays the final visual dashboard with Milestone status.

---

## `testforge ci`
CI/CD Headless Mode: Generate tests only for modified files and their dependents.

```bash
testforge ci [OPTIONS]
```

**Options**:
- `--project-root PATH`: Project root directory.
- `--base-branch TEXT`: Base branch to diff against. (Default: `main`)
- `--dry-run`: Output topological order without running.

!!! info "Under the Hood: Change Analysis"
    1.  **Git Diff**: Uses `GitPython` to identify files changed between the current HEAD and the `base-branch`.
    2.  **Impact Analysis**: Consults the dependency graph to find all modules that import the changed files (downstream dependents).
    3.  **Targeted Run**: Executes the `run-all` logic **only** on this subset of modules, ensuring PRs are verified without re-testing the entire codebase.

---

## `testforge generate`
Generates and validates a unit test suite for a single file.

```bash
testforge generate [FILE_PATH] [OPTIONS]
```

**Arguments**:
- `FILE_PATH`: The file to generate tests for.

**Options**:
- `--project-root PATH`: Project root directory.
- `--planner-model TEXT`: LLM model for the planning phase.
- `--coder-model TEXT`: LLM model for the coding phase.
- `--dry-run`: Estimate tokens and cost without running AI.

!!! info "Under the Hood: Single-File Logic"
    1.  **Isolation**: Clears the AI context to prevent "leaking" information from previous files.
    2.  **Deterministic Preview**: Summarizes the module's complexity and interface before calling the LLM.
    3.  **Self-Healing Loop**: Runs up to 3 repair attempts if `pytest` fails, feeding the traceback directly back to the AI.

---

## `testforge refactor-fixtures`
Scans test files and elevates local fixtures to `conftest.py`.

```bash
testforge refactor-fixtures [OPTIONS]
```

**Options**:
- `--project-root PATH`: Project root directory.
- `--coder-model TEXT`: LLM model for the refactoring phase.

!!! info "Under the Hood: Global Elevation"
    1.  **Discovery**: Recursively scans the `tests/` directory for all files matching `test_*.py`.
    2.  **State Initialization**: Ensures a `tests/conftest.py` file exists to act as the destination.
    3.  **Cross-File Analysis**: Loads all test files and the `conftest.py` into the LLM's context.
    4.  **Deduplication**: The AI identifies `@pytest.fixture` definitions that are duplicated or highly similar across multiple files.
    5.  **Refactoring**: 
        *   Extracts the fixtures to `conftest.py`.
        *   Removes local definitions from individual test files.
        *   Updates imports and references to ensure tests remain functional and "dry".
