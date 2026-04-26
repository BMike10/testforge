# Scientific Core & Methodology 🔬

TestForge is built on rigorous computer science principles to ensure that AI-generated tests are not just "hallucinations" of code, but valid engineering artifacts.

## 1. Topological Dependency Resolution
**The Problem**: Testing a high-level module before its dependencies leads to complex mocking requirements and "context bloat" in AI prompts.

**The Solution**: TestForge builds a Directed Acyclic Graph (DAG) of your entire codebase using AST.
- It identifies "leaf" modules (those with no internal dependencies).
- It generates tests bottom-up.
- When testing a module, it knows exactly which internal components to mock because they have already been verified.

## 2. McCabe Cyclomatic Complexity
**The Problem**: Not all code is created equal. Simple getters don't need the same rigor as complex nested logic.

**The Solution**: We calculate the complexity score ($M = E - N + 2P$) for every function and class.
- **Risk-Based Prioritization**: The AI is explicitly tasked to prioritize high-complexity paths.
- **Resource Allocation**: You can use heavier, more expensive reasoning models specifically for high-complexity modules.

## 3. Boundary Value Analysis (BVA)
**The Problem**: AI often tests "happy paths" and misses edge cases.

**The Solution**: TestForge forces the AI to define equivalence classes and explicitly test $n-1$, $n$, and $n+1$ boundaries for every input parameter. This ensures robustness against off-by-one errors and overflow conditions.

## 4. Dynamic Symbolic Execution (DSE) Simulation
**The Problem**: Branch coverage is often missed by stochastic generation.

**The Solution**: We prompt the AI to simulate a DSE engine. It must map out every logical branch (if/else, try/except) and then generate specific inputs designed to traverse each unique path.

## 5. Mutation-Guided Hardening
**The Problem**: Line coverage is a "vanity metric." You can have 100% coverage with zero meaningful assertions.

**The Solution**: We use `mutmut` to inject semantic faults (mutants) into your source code.
- If a test suite passes but a mutant survives, the test is empirically weak.
- TestForge feeds the surviving mutant's location and type back to the AI.
- The AI is tasked with hardening the assertions to "kill" the mutant.
