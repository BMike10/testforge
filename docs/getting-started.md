# Getting Started 🚀

## Installation

### Prerequisites
- Python >= 3.10
- Git

### Install from Source
```bash
git clone https://github.com/BMike10/testforge/
cd testforge
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Environment Configuration

TestForge is model-agnostic and works with both cloud-based LLMs (OpenAI, Anthropic) and local-first models (via vLLM, LM Studio, Ollama).

### Local LLM Setup (Recommended)
Local models like `Qwen-2.5-Coder` or `DeepSeek-V3` offer high performance with strict privacy.

Create a `.env` file in your project root:

```bash
# Local API Base (LM Studio, vLLM, etc.)
export LLM_API_BASE="http://127.0.0.1:1234/v1"

# Default Model name
export LLM_MODEL_NAME="mistralai/ministral-3-14b-reasoning"

# API Key (use 'no-key' for local servers)
export LLM_API_KEY="no-key"
```

### Cloud LLM Setup
For OpenAI or other providers, simply provide the API key and model name.

```bash
export LLM_MODEL_NAME="gpt-4o"
export LLM_API_KEY="sk-..."
```

---

## Quick Start in 3 Steps

1.  **Map your project**:
    ```bash
    testforge map src/
    ```
2.  **Plan tests for a module**:
    ```bash
    testforge plan src/core/logic.py
    ```
3.  **Generate and validate**:
    ```bash
    testforge generate src/core/logic.py
    ```

Ready for more? Check out the [CLI Reference](cli-reference.md).
