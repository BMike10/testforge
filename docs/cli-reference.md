# CLI Reference 🛠️

Detailed documentation for the TestForge command-line interface.

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

---

## `testforge plan`
Generates a 'Scientific Test Plan' for a specific module.

```bash
testforge plan [FILE_PATH] [OPTIONS]
```

**Arguments**:
- `FILE_PATH`: The specific file to plan tests for.

**Options**:
- `--project-root PATH`: Project root directory.
- `--planner-model TEXT`: LLM model for the planning phase.
- `--dry-run`: Estimate tokens and cost without running AI.

---

## `testforge generate`
Generates and validates a unit test suite using the AI-Judge loop.

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
- `--force`: Force run by clearing the execution ledger.
- `--dry-run`: Output topological order without running.

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

---

## `testforge refactor-fixtures`
Scans test files and elevates local fixtures to `conftest.py`.

```bash
testforge refactor-fixtures [OPTIONS]
```

**Options**:
- `--project-root PATH`: Project root directory.
- `--coder-model TEXT`: LLM model for the refactoring phase.
