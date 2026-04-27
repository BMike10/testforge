# 🛠️ TestForge: Scientifically Validated AI Test Generation

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/License-Apache%202.0-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Framework-Aider-orange.svg" alt="Framework">
  <a href="https://your-repo.github.io/testforge/"><img src="https://img.shields.io/badge/Docs-MkDocs-blueviolet.svg" alt="Documentation"></a>
</p>

**TestForge** is a high-integrity CLI framework that combines **Deterministic Static Analysis** with **Agentic AI** (powered by Aider) to generate, validate, and harden Python unit test suites.

It moves beyond simple line coverage by employing **McCabe Cyclomatic Complexity**, **Topological Dependency Resolution**, and **Mutation Testing** to ensure tests are structurally sound and behaviorally rigorous.

---

## 🔬 Core Methodology

- **Topological Sorting**: Builds a DAG of your codebase to test leaf modules first, preventing circular reasoning.
- **Complexity Analysis**: Deterministically calculates McCabe metrics to prioritize testing for high-risk code.
- **Mutation-Guided**: Uses fault injection (`mutmut`) to harden tests until they can empirically "kill" mutants.
- **BVA & DSE**: Forces AI to test boundary values and simulate path execution.

---

## 🚀 Quick Start

```bash
# Install
pip install git+https://github.com/your-repo/testforge.git

# Map your project
testforge map src/

# Plan and Generate tests for a file
testforge generate src/core/logic.py
```

---

## 📖 Documentation

For full installation guides, advanced configuration, and methodology deep dives, visit our documentation site:

👉 **[Read the Full Documentation](https://bmike10.github.io/testforge)**

---

## 📄 License

Apache 2.0
