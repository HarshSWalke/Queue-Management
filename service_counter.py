# service_counter.py
from typing import List, Optional

class ServiceCounterManager:
    """
    Manages available service counters as a stack.
    Push when a counter becomes free, pop to assign to a customer.
    """
    def __init__(self):
        self.available = []  # stack of counter ids

    def push_counter(self, counter_id: str):
        """Add an available service counter"""
        if counter_id in self.available:
            return
        self.available.append(counter_id)

    def pop_counter(self) -> Optional[str]:
        """Assign next counter to the next customer (LIFO). Returns counter id or None."""
        if not self.available:
            return None
        return self.available.pop()

    def available_counters(self) -> List[str]:
        """Return a list of available counters (top of stack is last element)."""
        return list(self.available)

    def to_dict(self):
        return {"available": list(self.available)}

    def load_from_dict(self, data):
        self.available = list(data.get("available", []))
