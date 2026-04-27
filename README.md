# 🛠️ TestForge: Scientifically Validated AI Test Generation

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Framework-Aider-orange.svg" alt="Framework">
  <a href="https://your-repo.github.io/testforge/"><img src="https://img.shields.io/badge/Docs-MkDocs-blueviolet.svg" alt="Documentation"></a>
</p>

**TestForge** is a high-integrity CLI framework that bridges the gap between **Deterministic Static Analysis** and **Agentic AI**. It doesn't just "write tests"—it builds behaviorally rigorous, scientifically validated test suites that you can trust.

---

## 💎 Why TestForge?

In a world of stochastic AI generation, TestForge enforces engineering discipline through a **Plan-First** architecture.

<table align="center">
  <tr>
    <td align="center"><b>Deterministic Filtering</b></td>
    <td align="center"><b>Topological Sorting</b></td>
    <td align="center"><b>Mutation Hardening</b></td>
  </tr>
  <tr>
    <td>Skips logic-less boilerplate to save tokens and focus on high-risk code.</td>
    <td>Builds a DAG of your project to test dependencies bottom-up.</td>
    <td>Uses fault injection to prove your tests actually catch bugs.</td>
  </tr>
</table>

---

## 🚀 The TestForge Workflow

### 1. Map & Analyze
Build a mental model of your codebase's architecture and complexity.
```bash
testforge map .
```

### 2. Plan (Dry-Run)
Generate an editable **Execution Plan** to preview context size and costs.
```bash
testforge run-all . --dry-run
```

### 3. Execute & Validate
Run the self-healing pipeline to generate, run, and harden your tests.
```bash
testforge run-all .
```

---

## 🔬 Core Methodology

*   **McCabe Prioritization**: Focuses testing efforts on high-complexity paths.
*   **BVA & DSE Simulation**: Forces the AI to test boundary values and simulate path execution.
*   **Editable Execution Planning**: You have total control over the context and order via `execution_plan.yaml`.
*   **Visual Dashboards**: Track project health via Scientific Milestones (M1/M2/M3).

---

## 📖 Documentation

For deep dives into our scientific core and advanced configuration, visit our documentation:

👉 **[Read the Full Documentation](https://bmike10.github.io/testforge)**

---

## 📄 License

Apache 2.0
