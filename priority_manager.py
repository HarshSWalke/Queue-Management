# priority_manager.py
import heapq
import time
from typing import Tuple, Optional, List, Dict

class PriorityCustomer:
    """
    Data for priority queue customers.
    Higher priority_level means served earlier; we'll invert for heapq (min-heap).
    """
    def __init__(self, token:int, name:str, priority_level:int, timestamp:float, user_type:str):
        self.token = token
        self.name = name
        self.priority_level = priority_level
        self.timestamp = timestamp
        self.type = user_type  # 'VIP' or 'Emergency'

    def to_dict(self) -> Dict:
        return {
            "token": self.token,
            "name": self.name,
            "priority_level": self.priority_level,
            "timestamp": self.timestamp,
            "type": self.type
        }

class PriorityManager:
    """
    Handles priority customers using heapq. Priority levels: larger -> higher priority.
    """
    def __init__(self):
        self.heap = []  # stores tuples (priority_sort_key, count, PriorityCustomer)
        self._counter = 0  # tie-breaker to preserve FIFO for equal priority
        self.token_map = {}  # token -> PriorityCustomer

    def add_priority_customer(self, token:int, name:str, priority_level:int, user_type:str) -> PriorityCustomer:
        """
        Add VIP or emergency customers.
        priority_level: integer (e.g., 1 normal, 5 VIP, 10 emergency). Larger -> higher priority.
        Returns PriorityCustomer.
        """
        self._counter += 1
        pc = PriorityCustomer(token, name, priority_level, time.time(), user_type)
        # Use negative priority_level so highest gets smallest -priority_level (min-heap).
        heapq.heappush(self.heap, (-priority_level, self._counter, pc))
        self.token_map[token] = pc
        return pc

    def get_next_priority_customer(self) -> Optional[PriorityCustomer]:
        """
        Pop and return the highest priority customer, or None if none exist.
        """
        if not self.heap:
            return None
        _, _, pc = heapq.heappop(self.heap)
        self.token_map.pop(pc.token, None)
        return pc

    def peek_all(self) -> List[Dict]:
        """
        Return list representation of all priority customers (sorted by priority and insertion).
        """
        items = sorted(self.heap, reverse=False)  # since stored as (-priority, counter,...)
        return [tup[2].to_dict() for tup in items]

    def remove_by_token(self, token:int):
        """
        Lazy removal: mark removed by popping until found; rebuild heap if needed.
        Simpler approach: rebuild heap without the token.
        """
        if token not in self.token_map:
            return None
        removed = self.token_map.pop(token)
        # rebuild heap without token
        self.heap = [t for t in self.heap if t[2].token != token]
        heapq.heapify(self.heap)
        return removed

    def to_dict(self) -> Dict:
        return {
            "heap": [tup[2].to_dict() for tup in sorted(self.heap, reverse=False)],
            "counter": self._counter
        }

    def load_from_dict(self, data: Dict):
        self.heap = []
        self.token_map = {}
        self._counter = data.get("counter", 0)
        for i, d in enumerate(data.get("heap", [])):
            pc = PriorityCustomer(d['token'], d['name'], d['priority_level'], d['timestamp'], d.get('type','VIP'))
            self._counter += 1
            heapq.heappush(self.heap, (-pc.priority_level, self._counter, pc))
            self.token_map[pc.token] = pc
