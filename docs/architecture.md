# System Architecture 🏗️

TestForge is engineered as a high-integrity bridge between **Deterministic Static Analysis** and **Agentic AI**. It treats AI not as an autonomous author, but as a specialized engine guided by strict scientific constraints and a deterministic pipeline.

---

## High-Level System Components

The following diagram illustrates how TestForge orchestrates the interaction between the user, the AI agent layer, and the validation engine.

```mermaid
graph TD
    User([User CLI]) --> Core[TestForge Core Engine]
    
    subgraph Core [TestForge Core]
        Orchestrator[Orchestrator]
        Context[Context Manager]
        State[(State Ledger)]
        Orchestrator --> Context
        Orchestrator --> State
    end
    
    Core --> AI[AI Agent Layer]
    
    subgraph AI [AI Layer]
        Aider[Aider API Wrapper]
        Aider --> Server{LLM Server}
        Server --> Cloud[Cloud: OpenAI/Anthropic]
        Server --> Local[Local: vLLM/LM Studio/Ollama]
    end
    
    Core --> Validation[Validation Layer]
    
    subgraph Validation [Validation & Hardening]
        Pytest[Pytest Engine]
        Mutmut[Mutmut Hardening]
    end
    
    AI -.->|Generates/Repairs| Validation
    Validation -.->|Feedback Loop| AI
```

---

## Execution Data Flow

TestForge follows a strict **Research -> Plan -> Execute -> Validate** lifecycle. This sequence ensures that every line of code generated is grounded in the actual architecture of your project.

```mermaid
sequenceDiagram
    participant U as User
    participant T as TestForge
    participant A as AI Agent (Aider)
    participant V as Validation (Pytest)

    U->>T: run-all [PATH]
    Note over T: Deterministic Phase
    T->>T: AST Mapping & Dependency DAG
    T->>T: Bottom-Up Topological Sort
    
    loop For each Module
        Note over T: Strategy Phase
        T->>T: Extract Context & Complexity
        T->>A: Strategic Test Plan Request
        A-->>T: Plan (markdown)
        
        Note over T: Execution Phase
        T->>A: Code Generation Request
        A-->>T: Generated Test Suite
        
        Note over T: Validation Phase
        T->>V: Syntax & Pytest Run
        alt Failure
            V-->>T: Error Traceback (Truncated)
            T->>A: Repair Request (Enriched Context)
            A-->>T: Fixed Test Suite
        else Success
            T->>V: Mutation Testing (Mutmut)
            V-->>T: Survival Report
        end
        T->>T: Update State Ledger
    end
    T-->>U: Final Dashboard & Reports
```

---

## Core Components

### 1. TestForge Core Engine
The "Brain" of the operation. It handles the heavy lifting of understanding your code without using AI tokens.
*   **Orchestrator**: Manages the pipeline lifecycle, concurrency, and error handling.
*   **Context Manager**: Uses `libcst` and `ast` to map the codebase, calculate McCabe complexity, and build the Dependency DAG.
*   **State Ledger**: A persistent JSON-based checkpointing system that allows the pipeline to pause, resume, and skip already-validated modules.

### 2. AI Agent Layer (Aider)
We utilize **Aider** as our primary agentic engine. Aider provides a robust API for applying multi-file edits and maintaining a coherent "chat" context with the LLM. TestForge enriches Aider's prompts with deterministic data (like the architecture map and BVA requirements) to minimize hallucinations.

### 3. Validation Layer
A test is only valid if it survives the fire of execution.
*   **Pytest**: Runs the generated tests. TestForge captures and "smart-truncates" the output to keep repair prompts dense and cost-efficient.
*   **Mutmut**: Injects "mutants" (intentional bugs) into your source code to verify that the generated tests actually fail when the logic changes.

---

## Deployment & Privacy Models

TestForge is model-agnostic. You can choose the infrastructure that fits your security requirements:

| Component | Cloud-First (SaaS) | Local-First (Private) |
| :--- | :--- | :--- |
| **Logic Engine** | Local Machine | Local Machine |
| **AI Inference** | OpenAI / Anthropic | vLLM / LM Studio / Ollama |
| **API Protocol** | HTTPS (Encrypted) | Localhost (No Data Leaves) |
| **Performance** | High Reasoning | High Privacy / Zero Cost |

!!! tip "Hybrid Strategy"
    Many users use a fast local model (like `Qwen-2.5-Coder`) for the **Mapping Phase** and a heavy cloud model (like `o1-preview` or `gpt-4o`) for the **Strategic Planning Phase**.
