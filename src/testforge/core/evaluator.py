import subprocess
import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List

class Evaluator:
    """
    The 'Judge' that validates generated tests through execution and mutation testing.
    """

    @staticmethod
    def validate_syntax(test_file: Path) -> Dict[str, Any]:
        """
        Perform a static syntax check on the test file.
        Returns a dict with 'success' and 'error' if any.
        """
        try:
            with open(test_file, "r") as f:
                content = f.read()
            ast.parse(content)
            return {"success": True}
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"SyntaxError in {test_file.name} at line {e.lineno}: {e.msg}\nCode: {e.text}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def run_pytest(test_file: Path) -> Dict[str, Any]:
        """
        Run pytest on the given test file and capture results with smart truncation.
        """
        # We use --tb=short to keep tracebacks concise and --maxfail=3 to stop early on many failures.
        result = subprocess.run(
            ["pytest", str(test_file), "--tb=short", "--maxfail=3"],
            capture_output=True,
            text=True
        )
        
        stdout = result.stdout
        stderr = result.stderr
        
        # Smart truncation: Extract FAILURES and ERRORS sections
        combined_output = stdout + stderr
        
        max_len = int(os.getenv("TESTFORGE_MAX_ERROR_LENGTH", "4000"))
        
        # Try to find the start of interesting sections
        patterns = [
            r"={10,}\s+FAILURES\s+={10,}",
            r"={10,}\s+ERRORS\s+={10,}",
            r"={10,}\s+short test summary info\s+={10,}"
        ]
        
        found_idx = -1
        for p in patterns:
            match = re.search(p, combined_output)
            if match:
                if found_idx == -1 or match.start() < found_idx:
                    found_idx = match.start()
        
        if found_idx != -1:
            smart_output = combined_output[found_idx:]
            # Still truncate if the "smart" section is too huge
            if len(smart_output) > max_len:
                half_max = max_len // 2
                smart_output = smart_output[:half_max] + "\n... [TRUNCATED] ...\n" + smart_output[-half_max:]
        else:
            # Fallback to simple truncation
            if len(combined_output) > max_len:
                half_max = max_len // 2
                smart_output = combined_output[:half_max] + "\n... [TRUNCATED] ...\n" + combined_output[-half_max:]
            else:
                smart_output = combined_output

        return {
            "success": result.returncode == 0,
            "stdout": stdout,
            "stderr": stderr,
            "error_summary": smart_output
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
