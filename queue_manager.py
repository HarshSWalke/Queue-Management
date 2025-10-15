# queue_manager.py
from collections import deque
import time
from typing import List, Dict, Optional

class QueueItem:
    """
    Represents a user in the queue.
    """
    def __init__(self, token: int, name: str, user_type: str, timestamp: float):
        self.token = token
        self.name = name
        self.type = user_type  # 'Normal', 'VIP', 'Emergency'
        self.timestamp = timestamp  # time when token was issued

    def to_dict(self) -> Dict:
        return {
            "token": self.token,
            "name": self.name,
            "type": self.type,
            "timestamp": self.timestamp
        }

class QueueManager:
    """
    Manages the main queue (for Normal customers). Priority customers are handled
    by priority_manager but integrate through this manager.
    Uses deque for O(1) enqueue/dequeue.
    """
    def __init__(self, avg_service_time_seconds: int = 180):
        self.queue = deque()  # holds QueueItem for normal flow
        self.next_token = 1
        self.avg_service_time = max(1, avg_service_time_seconds)  # seconds per service (default 3 minutes)
        # mapping token -> QueueItem for quick lookup
        self.token_map = {}

    def enqueue(self, name: str, user_type: str='Normal') -> QueueItem:
        """
        Add user to queue with token and priority type.
        For Normal users this manager stores them; for others, priority_manager should be used.
        Returns QueueItem.
        """
        token = self.next_token
        self.next_token += 1
        item = QueueItem(token, name, user_type, time.time())
        self.queue.append(item)
        self.token_map[token] = item
        return item

    def dequeue(self) -> Optional[QueueItem]:
        """
        Serve the next customer from the normal queue. Returns the QueueItem or None if empty.
        """
        if not self.queue:
            return None
        item = self.queue.popleft()
        self.token_map.pop(item.token, None)
        return item

    def display_queue(self) -> List[Dict]:
        """
        Return current queue status as list of dicts (token, name, type, timestamp).
        """
        return [item.to_dict() for item in self.queue]

    def estimate_wait_time(self, token: Optional[int] = None) -> Dict:
        """
        Calculate and return estimated time based on average service time.
        If token is None, return estimate for full queue (total wait).
        If token provided, return user's position and estimated time in seconds.
        """
        if not self.queue:
            return {"position": 0, "estimated_seconds": 0}

        if token is None:
            total = len(self.queue) * self.avg_service_time
            return {"position": len(self.queue), "estimated_seconds": total}

        # find position
        for idx, item in enumerate(self.queue):
            if item.token == token:
                pos = idx  # 0-indexed; idx customers ahead
                return {"position": idx + 1, "estimated_seconds": (idx) * self.avg_service_time}
        return {"position": -1, "estimated_seconds": -1}  # not found

    def find_and_remove(self, token: int) -> Optional[QueueItem]:
        """
        Remove a user by token from the normal queue. Returns the removed item or None.
        """
        for idx, item in enumerate(self.queue):
            if item.token == token:
                removed = self.queue[idx]
                # remove by reconstructing deque without that index for simplicity
                self.queue.rotate(-idx)
                self.queue.popleft()
                self.queue.rotate(idx)
                self.token_map.pop(token, None)
                return removed
        return None

    def to_dict(self) -> Dict:
        """
        Serialize minimal state (for persistence).
        """
        return {
            "next_token": self.next_token,
            "avg_service_time": self.avg_service_time,
            "queue": [i.to_dict() for i in self.queue]
        }

    def load_from_dict(self, data: Dict):
        """
        Restore state from saved dict.
        """
        self.next_token = data.get("next_token", self.next_token)
        self.avg_service_time = data.get("avg_service_time", self.avg_service_time)
        self.queue = deque()
        self.token_map = {}
        for d in data.get("queue", []):
            item = QueueItem(d['token'], d['name'], d['type'], d['timestamp'])
            self.queue.append(item)
            self.token_map[item.token] = item
