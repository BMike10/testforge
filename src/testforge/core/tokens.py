import tiktoken
from pathlib import Path
from rich.console import Console

console = Console()

class TokenEstimator:
    @staticmethod
    def estimate_file_tokens(file_path: Path, model: str = "gpt-4o") -> int:
        if not file_path.exists():
            return 0
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return TokenEstimator.estimate_string_tokens(content, model)
        except Exception:
            return 0

    @staticmethod
    def estimate_string_tokens(content: str, model: str = "gpt-4o") -> int:
        try:
            # tiktoken might not support all model names, fallback to cl100k_base
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(content))
        except Exception:
            # Fallback heuristic: 1 token ~= 4 chars
            return len(content) // 4

    @staticmethod
    def print_cost_estimate(tokens: int, phase: str = "Generation"):
        # Rough estimate based on typical GPT-4o pricing (e.g., $5.00 / 1M input tokens)
        cost = (tokens / 1000000) * 5.00
        console.print(f"[cyan]{phase} Estimated Input Tokens:[/cyan] {tokens} (~${cost:.4f})")
