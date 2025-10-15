# file_handler.py
import json
from typing import Dict
from pathlib import Path

class FileHandler:
    """
    Save and load the queue system state to/from a JSON file.
    Each manager must provide to_dict() and load_from_dict() methods.
    """

    def __init__(self, filename: str = "smartqueue_state.json"):
        self.filename = Path(filename)

    def save_to_file(self, queue_manager, priority_manager, service_manager, analytics, undo_stack=None):
        """
        Persist current queue state.
        """
        state = {
            "queue_manager": queue_manager.to_dict(),
            "priority_manager": priority_manager.to_dict(),
            "service_manager": service_manager.to_dict(),
            "analytics": {"served_timestamps": getattr(analytics, "served_timestamps", [])},
            "undo_stack": getattr(undo_stack, "stack", [])
        }
        with open(self.filename, "w") as f:
            json.dump(state, f, indent=2)
        return str(self.filename.resolve())

    def load_from_file(self, queue_manager, priority_manager, service_manager, analytics, undo_stack=None):
        """
        Restore queue state from file. Returns True if loaded, False if file missing.
        """
        if not self.filename.exists():
            return False
        with open(self.filename, "r") as f:
            state = json.load(f)
        queue_manager.load_from_dict(state.get("queue_manager", {}))
        priority_manager.load_from_dict(state.get("priority_manager", {}))
        service_manager.load_from_dict(state.get("service_manager", {}))
        analytics.served_timestamps = state.get("analytics", {}).get("served_timestamps", [])
        if undo_stack is not None:
            undo_stack.stack = state.get("undo_stack", [])
        return True
