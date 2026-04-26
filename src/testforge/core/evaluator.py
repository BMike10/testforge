import subprocess
import os
from pathlib import Path
from typing import Dict, Any, List

class Evaluator:
    """
    The 'Judge' that validates generated tests through execution and mutation testing.
    """

    @staticmethod
    def run_pytest(test_file: Path) -> Dict[str, Any]:
        """
        Run pytest on the given test file and capture results.
        """
        result = subprocess.run(
            ["pytest", str(test_file), "--verbose"],
            capture_output=True,
            text=True
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    @staticmethod
    def run_mutation_testing(target_file: Path, test_file: Path) -> Dict[str, Any]:
        """
        Run mutation testing using mutmut.
        Note: This is a simplified wrapper. mutmut usually requires a config or specific setup.
        """
        # mutmut run --paths-to-mutate target_file --tests-dir test_file
        # This is high-level; real implementation needs careful integration with mutmut's state.
        result = subprocess.run(
            ["mutmut", "run", "--paths-to-mutate", str(target_file)],
            capture_output=True,
            text=True
        )
        
        # Parse mutmut results (e.g. from mutmut results command)
        show_result = subprocess.run(
            ["mutmut", "results"],
            capture_output=True,
            text=True
        )
        
        return {
            "output": show_result.stdout,
            "summary": "Mutation testing results captured."
        }
