from typing import List, Dict, Any

class OperationalTransform:
    """Service for handling operational transforms for collaborative editing."""

    @staticmethod
    def transform_operations(client_ops: List[Dict[str, Any]], server_ops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform client operations against server operations to resolve conflicts

        Args:
            client_ops: Operations from client
            server_ops: Operations from server that happened concurrently

        Returns:
            Transformed client operations
        """
        # Basic implementation - more sophisticated OT would be needed for production
        transformed_ops = []

        for client_op in client_ops:
            # Check for direct conflicts (same element being modified)
            conflicting_server_ops = [
                op for op in server_ops
                if op.get('id') == client_op.get('id')
            ]

            if not conflicting_server_ops:
                # No conflict, keep the operation as is
                transformed_ops.append(client_op)
            else:
                # Handle conflict based on operation types
                client_type = client_op.get('type')

                if client_type == 'delete':
                    # If server also deleted, skip client delete
                    if not any(op.get('type') == 'delete' for op in conflicting_server_ops):
                        transformed_ops.append(client_op)

                elif client_type == 'add':
                    # For adds, ensure unique ID if there's a conflict
                    if any(op.get('type') == 'add' for op in conflicting_server_ops):
                        # Generate new ID to avoid conflict
                        new_id = f"{client_op['id']}_new"
                        transformed_ops.append({
                            **client_op,
                            'id': new_id,
                            'data': {**client_op['data'], 'id': new_id}
                        })
                    else:
                        transformed_ops.append(client_op)

                elif client_type == 'update':
                    # For updates, merge changes with later timestamp winning
                    server_updates = [
                        op for op in conflicting_server_ops
                        if op.get('type') == 'update'
                    ]

                    if not server_updates:
                        transformed_ops.append(client_op)
                    else:
                        # Merge updates, with client changes taking precedence
                        # This is simplified - real OT would be more complex
                        merged = {**client_op}
                        transformed_ops.append(merged)

        return transformed_ops
