# Advanced Guide 🛡️

## The Execution Dashboard & Milestones
During a `run-all` execution, TestForge displays a real-time terminal dashboard powered by `rich`. This dashboard provides high-level visibility into the pipeline's progress and scientific health.

### Milestone Definitions
We track three specific milestones to ensure the generated test suite is robust:

*   **M1 Core >= 80%**: Triggered when at least 80% of the testable modules have a "completed" status in the ledger. This indicates the primary logic of the project is covered.
*   **M2 P0 >= 90%**: Triggered when 90% of modules are validated. This typically covers all critical path components.
*   **M3 Suite Stable**: Triggered only when 100% of modules are validated and there are **zero** failed modules in the ledger.

---

## Editable Execution Planning (YAML Overrides)
TestForge follows a "Plan-First" philosophy. By using the `--dry-run` flag with `run-all`, you can generate an `execution_plan.yaml` file that allows you to manually control the pipeline before any LLM tokens are spent.

### Why use an Execution Plan?
1.  **Context Tuning**: Remove large, noisy files from a module's context to reduce costs.
2.  **Custom Ordering**: Reorder the pipeline if you have specific testing priorities.
3.  **Output Redirection**: Manually change where the generated test files will be saved.

### Sample `execution_plan.yaml`
```yaml
execution_order:
  - src/testforge/utils/env_setup.py
  - src/testforge/core/context.py
phases:
  Phase_1:
    module: src/testforge/utils/env_setup.py
    context_files:
      - src/testforge/utils/env_setup.py
    expected_output: tests/test_env_setup.py
  Phase_2:
    module: src/testforge/core/context.py
    context_files:
      - src/testforge/core/context.py
      - src/testforge/utils/env_setup.py  # Dependency added by graph logic
    expected_output: tests/test_context.py
```

!!! tip "Manual Override"
    To use your custom plan, simply run `testforge run-all .` without the `--dry-run` flag. TestForge will detect the YAML file and use it as the source of truth for the execution sequence.

---

## The Execution Ledger (State Management)
TestForge maintains a persistent state file at `.testforge/ledger.json` in your project root.

!!! info "Under the Hood: Ledger Schema"
    The ledger tracks every module by its relative path:
    *   **Status: completed**: Module passed `pytest` and mutation tests. It will be skipped in future runs.
    *   **Status: failed**: Module failed validation or hit the retry limit.
    *   **Error**: Stores the last traceback or error message for failed modules.

To ignore the ledger and restart the entire pipeline, use the `--force` flag.

---

## Dynamic Model Routing
You can optimize costs and performance by routing different phases to different models.

=== "CLI Override"
    ```bash
    testforge run-all . --mapper-model gpt-4o-mini --planner-model o1-preview --coder-model gpt-4o
    ```

=== "Environment Variables"
    ```bash
    export LLM_MAPPER_MODEL="gpt-4o-mini"
    export LLM_PLANNER_MODEL="o1-preview"
    export LLM_CODER_MODEL="gpt-4o"
    ```

---

## Template Overrides
Every LLM interaction is based on Jinja2 templates. You can customize these to enforce your company's coding standards or add specific scientific constraints.

### The Overriding Logic
TestForge searches for templates in the following order of priority:
1.  **Custom Directory**: The path specified in the `TESTFORGE_TEMPLATES_DIR` environment variable.
2.  **Project Root**: The `.testforge/templates/` folder in your project root.
3.  **Package Defaults**: The internal templates bundled with the library.

### How to Customize
The easiest way to start customizing is to "eject" the default templates into your workspace:

```bash
testforge init-templates
```

This command will copy the top-level `.j2` templates into your `.testforge/templates/` directory. 

!!! info "Template Inheritance"
    Default templates now use Jinja2 inheritance. For example, `plan_tests.j2` contains:
    ```jinja2
    {% extends "base/base_plan_tests.j2" %}
    ```
    This means you can customize specific parts of the prompt by overriding `{% block %}` sections (e.g., `critical_instructions`) while keeping the core logic intact.

### Strict Validation & Drift Detection
TestForge employs **Smart Template Validation** to ensure reliability:
*   **Strict Mode**: If a template expects a variable that isn't provided by the code, TestForge will raise an error immediately.
*   **AST Drift Detection**: TestForge uses AST analysis to identify variables passed from the code that are *not* used in your custom template. If drift is detected, a warning will be emitted.

### Available Templates
| Template | Purpose | Key Context Variables |
| :--- | :--- | :--- |
| `plan_tests.j2` | Generates the Scientific Test Plan. | `module_path`, `module_code`, `architecture_map`, `deterministic_context`, `plan_file` |
| `generate_test_suite.j2` | Generates the actual `pytest` code. | `plan_path`, `module_path`, `test_path` |
| `repair_test_suite.j2` | Used in the self-healing loop to fix failing tests. | `test_path`, `error_output` |
| `summarize_architecture.j2` | Summarizes the architecture for the mapper phase. | `architecture_map` |
