import json
from pathlib import Path
from typing import Dict, Any

class StateTracker:
    """
    Manages the Execution Ledger to track the pipeline state and resume interrupted runs.
    """
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ledger_dir = self.project_root / ".testforge"
        self.ledger_file = self.ledger_dir / "ledger.json"
        
        if not self.ledger_dir.exists():
            self.ledger_dir.mkdir(parents=True, exist_ok=True)
            
        self.state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"modules": {}}
        return {"modules": {}}

    def _save(self):
        with open(self.ledger_file, "w") as f:
            json.dump(self.state, f, indent=4)

    def mark_completed(self, module_path: str):
        if "modules" not in self.state:
            self.state["modules"] = {}
        self.state["modules"][module_path] = {"status": "completed"}
        self._save()

    def mark_failed(self, module_path: str, error: str = ""):
        if "modules" not in self.state:
            self.state["modules"] = {}
        self.state["modules"][module_path] = {"status": "failed", "error": error}
        self._save()

    def is_completed(self, module_path: str) -> bool:
        module_state = self.state.get("modules", {}).get(module_path)
        if module_state and module_state.get("status") == "completed":
            return True
        return False

    def clear(self):
        self.state = {"modules": {}}
        self._save()
