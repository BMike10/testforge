# Welcome to TestForge 🛠️

**Scientifically Validated AI Test Generation**

TestForge is a high-integrity CLI framework that combines **Deterministic Static Analysis** with **Agentic AI** to generate, validate, and harden Python unit test suites. 

It moves beyond simple line coverage by employing McCabe Cyclomatic Complexity, Topological Dependency Resolution, and Mutation Testing to ensure tests are structurally sound and behaviorally rigorous.

---

## The TestForge Philosophy

In the era of AI-assisted coding, generating tests is easy, but generating *correct* and *rigorous* tests is hard. TestForge is built on the belief that AI should be guided by deterministic engineering principles:

<div class="grid cards" markdown>

-   :material-brain: __Don't Guess, Analyze__

    ---

    We use AST analysis to understand your code's structure before the AI ever sees it. No hallucinations, just symbols.

-   :material-chart-bell-curve: __Complexity Matters__

    ---

    McCabe metrics prioritize testing for high-risk paths. We spend your LLM tokens where they are needed most.

-   :material-bug-check: __Verify the Verification__

    ---

    Mutation Testing proves your tests actually work. If a test can't kill a mutant, it's not a valid engineering artifact.

</div>

---

## How It Works (Under the Hood)

TestForge operates on a continuous **Research -> Plan -> Generate -> Validate** lifecycle:

1.  **Map**: Scans the project to build a Dependency DAG and complexity map.
2.  **Plan**: Generates an editable `execution_plan.yaml` during dry-run for human review.
3.  **Execute**: AI generates tests following a strict "Scientific Plan" for each module.
4.  **Harden**: `mutmut` injects faults to ensure the test suite is behaviorally rigorous.

[Get Started with TestForge](getting-started.md){ .md-button .md-button--primary }
[Deep Dive: Methodology](methodology.md){ .md-button }
