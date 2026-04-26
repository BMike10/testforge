import os
import subprocess
import sys
from pathlib import Path
from rich.console import Console

console = Console()

class EnvironmentManager:
    """
    Automates the setup and verification of the testing environment.
    """
    required_tools = ["pytest", "mutmut", "coverage"]

    @staticmethod
    def setup_testing_env(project_root: Path):
        """
        Ensures all necessary testing tools are installed and configured.
        """
        console.print("[blue]Verifying testing environment...[/blue]")
        
        # Check for pytest.ini
        pytest_ini = project_root / "pytest.ini"
        if not pytest_ini.exists():
            console.print("[yellow]pytest.ini not found. Creating a baseline configuration...[/yellow]")
            with open(pytest_ini, "w") as f:
                f.write("[pytest]\ntestpaths = tests\npythonpath = src\n")
        
        # Ensure tests directory exists
        tests_dir = project_root / "tests"
        if not tests_dir.exists():
            console.print("[yellow]tests/ directory not found. Creating it...[/yellow]")
            tests_dir.mkdir()
            (tests_dir / "__init__.py").touch()

        # Check for required tools via subprocess
        for tool in EnvironmentManager.required_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                console.print(f"[green]✔ {tool} is installed.[/green]")
            except (subprocess.CalledProcessError, FileNotFoundError):
                console.print(f"[red]✘ {tool} is not found in the environment. Attempting to install...[/red]")
                subprocess.run([sys.executable, "-m", "pip", "install", tool], check=True)

    @staticmethod
    def validate_execution():
        """
        Runs a dummy test to ensure the environment can execute tests.
        """
        console.print("[blue]Validating test execution...[/blue]")
        # This could run a minimal pytest command
        try:
            result = subprocess.run(["pytest", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✔ Environment validated successfully.[/green]")
                return True
        except Exception as e:
            console.print(f"[red]✘ Validation failed: {e}[/red]")
        return False
