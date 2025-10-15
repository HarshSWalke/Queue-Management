# user_search.py
from typing import Dict, Optional, Tuple
import time

class UserSearch:
    """
    Helps find and remove users quickly using token lookup.
    The main queue and priority manager should keep synchronized token maps.
    This module provides utility functions that operate on provided maps.
    """

    @staticmethod
    def find_user_by_token(token:int, normal_token_map:Dict[int, object], priority_token_map:Dict[int, object], queue_manager=None):
        """
        Return a tuple (location, type, position, estimated_seconds)
        location: 'normal', 'priority', or 'not_found'
        type: user type name
        position: index or rank in corresponding queue (1-based), -1 if unknown
        estimated_seconds: approximate wait (seconds) based on queue_manager.avg_service_time if provided, else -1
        """
        if token in normal_token_map:
            item = normal_token_map[token]
            # find position in queue_manager
            pos_info = queue_manager.estimate_wait_time(token) if queue_manager else {"position": -1, "estimated_seconds": -1}
            return ("normal", item.type, pos_info["position"], pos_info["estimated_seconds"])
        if token in priority_token_map:
            # position in priority queue - approximate by ranking priority
            # priority_token_map values are PriorityCustomer objects, we only know they exist
            # We'll return position as unknown (-1) unless caller provides priority_manager for ranking
            item = priority_token_map[token]
            return ("priority", item.type, -1, -1)
        return ("not_found", None, -1, -1)

    @staticmethod
    def remove_user(token:int, queue_manager, priority_manager):
        """
        Remove user by token from either normal or priority queues. Returns removed item or None.
        """
        if token in queue_manager.token_map:
            return queue_manager.find_and_remove(token)
        if token in priority_manager.token_map:
            return priority_manager.remove_by_token(token)
        return None
