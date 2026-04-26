# Advanced Guide 🛡️

## Dynamic Model Routing
TestForge allows you to route different phases to different models. This is useful for balancing cost and reasoning capability.

- **Phase 1 (Mapping)**: Use a fast, cost-effective model (e.g., `gpt-4o-mini` or a small local model).
- **Phase 2 (Planning)**: Use a reasoning-heavy model (e.g., `o1-preview` or `DeepSeek-R1`).
- **Phase 3 (Generation)**: Use a balanced coding model (e.g., `gpt-4o` or `Qwen-2.5-Coder-32B`).

### Configuration via Environment
```bash
export LLM_MAPPER_MODEL="gpt-4o-mini"
export LLM_PLANNER_MODEL="o1-preview"
export LLM_CODER_MODEL="gpt-4o"
```

### Configuration via CLI
```bash
testforge run-all . --mapper-model gpt-4o-mini --planner-model o1-preview --coder-model gpt-4o
```

---

## Template Overrides
Every LLM interaction in TestForge is based on Jinja2 templates. You can customize these to enforce your company's coding standards.

1.  Create a folder named `.testforge/templates/` in your project root.
2.  Copy any default template from the TestForge source (e.g., `plan_tests.j2`).
3.  Modify the copy. TestForge will now prioritize your local version.

---

## The Execution Ledger (State Management)
During a `run-all` execution, TestForge maintains a state file at `.testforge/ledger.json`.

- **Persistence**: If the process crashes or is interrupted, TestForge will resume from the last unverified module.
- **Verification**: Only modules that pass `pytest` and optional mutation tests are marked as `completed`.
- **Force Reset**: To ignore the ledger and restart from scratch, use the `--force` flag.

---

## Fixture Isolation
To prevent a "global blast radius," TestForge's AI generates local fixtures within individual test files. Once you have a stable suite, use `testforge refactor-fixtures` to safely elevate shared fixtures to a global `conftest.py`.
