# Contributing to TestForge 🤝

We welcome contributions from the community! Whether you're fixing bugs, adding new features, or improving documentation, your help is appreciated.

## Development Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-repo/testforge.git
    cd testforge
    ```
2.  **Install in editable mode with development dependencies**:
    ```bash
    pip install -e ".[docs]"
    ```
3.  **Run tests**:
    ```bash
    pytest
    ```

## Coding Standards
- Use **Type Hints** for all function signatures.
- Adhere to **PEP 8** styling.
- Ensure all new features are covered by **unit tests**.
- Update **documentation** if you change CLI behavior.

## Pull Request Process
1.  Create a new branch for your feature or bugfix.
2.  Commit your changes with descriptive messages.
3.  Submit a PR and describe the impact of your changes.
4.  Ensure all CI checks pass.

## License
TestForge is licensed under the Apache 2.0 License.
