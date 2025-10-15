# undo_stack.py
from typing import List, Dict, Any, Optional

class UndoStack:
    """
    Stores operations to allow undoing last operation.
    Each operation is a dict with:
      - action: 'enqueue'|'dequeue'|'remove'|'serve_priority'
      - data: operation-specific payload needed to revert
    """
    def __init__(self):
        self.stack: List[Dict[str, Any]] = []

    def push_operation(self, action:str, data:Dict):
        """
        Store the last action.
        action: name of action
        data: payload necessary to undo
        """
        self.stack.append({"action": action, "data": data})

    def undo_last_operation(self, queue_manager, priority_manager, service_manager):
        """
        Revert previous serve/remove/enqueue action.
        Returns a description of what was undone or None if no actions.
        """
        if not self.stack:
            return None
        op = self.stack.pop()
        action = op['action']
        data = op['data']
        # handle rewind logic for common actions
        if action == 'enqueue':
            # revert enqueue -> remove token if still present
            token = data.get('token')
            removed = queue_manager.find_and_remove(token)
            return {"undone": "enqueue", "token": token, "item": removed.to_dict() if removed else None}
        elif action == 'dequeue':
            # revert dequeue -> put item back to front of queue
            item = data.get('item')
            if item:
                # create object-like again
                # insert at left
                queue_manager.queue.appendleft(queue_manager.QueueItem if hasattr(queue_manager, 'QueueItem') else None)
                # simpler: we will reconstruct QueueItem using queue_manager internals
                # However to avoid complexity, we will re-create a QueueItem using the module's class
                from queue_manager import QueueItem  # local import to avoid cycle in top-level
                qitem = QueueItem(item['token'], item['name'], item['type'], item['timestamp'])
                queue_manager.queue.appendleft(qitem)
                queue_manager.token_map[qitem.token] = qitem
                return {"undone": "dequeue", "token": qitem.token}
            return {"undone": "dequeue", "info": "no item data"}
        elif action == 'remove':
            # revert a remove by reinserting based on original container
            item = data.get('item')
            container = data.get('container')  # 'normal' or 'priority'
            if not item:
                return {"undone": "remove", "info": "no item data"}
            if container == 'normal':
                from queue_manager import QueueItem
                qitem = QueueItem(item['token'], item['name'], item['type'], item['timestamp'])
                queue_manager.queue.append(qitem)  # append back to tail
                queue_manager.token_map[qitem.token] = qitem
                return {"undone": "remove", "token": qitem.token}
            elif container == 'priority':
                # re-add priority
                priority_manager.add_priority_customer(item['token'], item['name'], item['priority_level'], item.get('type','VIP'))
                return {"undone": "remove_priority", "token": item['token']}
            else:
                return {"undone": "remove", "info": "unknown container"}
        else:
            return {"undone": "unknown_action", "action": action}
