# Welcome to TestForge 🛠️

**Scientifically Validated AI Test Generation**

TestForge is a high-integrity CLI framework that combines **Deterministic Static Analysis** with **Agentic AI** to generate, validate, and harden Python unit test suites. 

It moves beyond simple line coverage by employing McCabe Cyclomatic Complexity, Topological Dependency Resolution, and Mutation Testing to ensure tests are structurally sound and behaviorally rigorous.

---

## The TestForge Philosophy

In the era of AI-assisted coding, generating tests is easy, but generating *correct* and *rigorous* tests is hard. TestForge is built on the belief that AI should be guided by deterministic engineering principles:

- **Don't Guess, Analyze**: We use AST analysis to understand your code's structure before the AI ever sees it.
- **Complexity Matters**: Higher complexity code needs more tests. We prioritize testing where it's needed most.
- **Verify the Verification**: We use Mutation Testing to ensure your tests actually catch bugs.

---

## Core Methodology at a Glance

1.  **Topological Sort**: Tests dependencies first, then components.
2.  **McCabe Complexity**: Identifies high-risk paths for priority testing.
3.  **BVA & DSE**: Forces AI to test boundaries and simulate execution paths.
4.  **Self-Healing Loop**: Automatically repairs tests that fail validation.
5.  **Mutation Hardening**: Injects faults to prove test rigor.

[Get Started with TestForge](getting-started.md){ .md-button .md-button--primary }
