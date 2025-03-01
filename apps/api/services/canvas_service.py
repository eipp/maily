from typing import Dict, List, Any, Optional, Union, Tuple
import asyncio
import json
import uuid
from loguru import logger
from datetime import datetime

from ..models.canvas import CanvasOperation, OperationTransform, CanvasState
from ..database.mongodb import get_database
from ..cache.redis_client import get_redis_client

class CanvasService:
    """
    Service for handling canvas operations and state management.
    Implements Operational Transformation (OT) for collaborative editing.
    """

    def __init__(self):
        self.db = None
        self.redis = None
        self.lock = asyncio.Lock()
        self.canvas_locks = {}  # Per-canvas locks

    async def initialize(self):
        """Initialize the service with database and cache connections"""
        self.db = await get_database()
        self.redis = await get_redis_client()
        logger.info("Canvas service initialized")

    async def close(self):
        """Close connections"""
        # No explicit close needed for MongoDB client
        if self.redis:
            await self.redis.close()
        logger.info("Canvas service connections closed")

    async def get_canvas_lock(self, canvas_id: str) -> asyncio.Lock:
        """Get a lock specific to this canvas"""
        async with self.lock:
            if canvas_id not in self.canvas_locks:
                self.canvas_locks[canvas_id] = asyncio.Lock()
            return self.canvas_locks[canvas_id]

    async def get_canvas_state(self, canvas_id: str) -> Dict[str, Any]:
        """Get the current state of a canvas"""
        try:
            # Try from Redis cache first
            cache_key = f"canvas:state:{canvas_id}"
            cached_state = await self.redis.get(cache_key)

            if cached_state:
                return json.loads(cached_state)

            # If not in cache, fetch from database
            canvas_collection = self.db.canvases
            canvas = await canvas_collection.find_one({"id": canvas_id})

            if not canvas:
                # Canvas not found, return minimal state
                return {"id": canvas_id, "version": 0, "elements": {}}

            # Cache for future requests (60 seconds TTL)
            await self.redis.set(
                cache_key,
                json.dumps(canvas),
                expire=60
            )

            return canvas
        except Exception as e:
            logger.error(f"Error getting canvas state: {e}")
            return {"id": canvas_id, "version": 0, "error": str(e)}

    async def get_operations_since(self, canvas_id: str, version: int) -> List[Dict[str, Any]]:
        """Get all operations for a canvas since a specific version"""
        try:
            operations_collection = self.db.canvas_operations
            operations = await operations_collection.find(
                {"canvas_id": canvas_id, "version": {"$gt": version}}
            ).sort("version", 1).to_list(length=1000)  # Limit to prevent too many operations

            return operations
        except Exception as e:
            logger.error(f"Error getting operations: {e}")
            return []

    async def save_canvas_state(self, canvas_id: str, state: Dict[str, Any]):
        """Save canvas state to database and update cache"""
        try:
            canvas_collection = self.db.canvases

            # Ensure updated_at is set
            state["updated_at"] = datetime.utcnow()

            # Update or insert
            await canvas_collection.update_one(
                {"id": canvas_id},
                {"$set": state},
                upsert=True
            )

            # Update cache
            cache_key = f"canvas:state:{canvas_id}"
            await self.redis.set(
                cache_key,
                json.dumps(state),
                expire=60
            )

            logger.debug(f"Canvas state saved for {canvas_id}, version {state.get('version', 0)}")
            return True
        except Exception as e:
            logger.error(f"Error saving canvas state: {e}")
            return False

    async def save_operations(self, canvas_id: str, operations: List[CanvasOperation], base_version: int, new_version: int):
        """Save operations to the database"""
        try:
            operations_collection = self.db.canvas_operations

            # Convert operations to database format
            ops_to_save = []
            version = base_version

            for op in operations:
                version += 1
                op_dict = op.dict()
                op_dict["canvas_id"] = canvas_id
                op_dict["version"] = version
                op_dict["timestamp"] = datetime.utcnow()
                ops_to_save.append(op_dict)

            if ops_to_save:
                await operations_collection.insert_many(ops_to_save)

            logger.debug(f"Saved {len(ops_to_save)} operations for canvas {canvas_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving operations: {e}")
            return False

    async def apply_operations(
        self,
        canvas_id: str,
        operations: List[CanvasOperation],
        base_version: int,
        user_id: str
    ) -> Optional[OperationTransform]:
        """Apply operations to canvas using operational transformation"""
        # Get a lock specific to this canvas
        canvas_lock = await self.get_canvas_lock(canvas_id)

        # Acquire lock to ensure sequential processing
        async with canvas_lock:
            try:
                # Get the current state
                state = await self.get_canvas_state(canvas_id)
                current_version = state.get("version", 0)

                # Check if operations are already applied or need transformation
                if base_version > current_version:
                    logger.warning(f"Base version {base_version} is higher than current version {current_version}")
                    return None

                # Check if base version is outdated
                needs_transform = base_version < current_version
                transformed_operations = None

                if needs_transform:
                    # Get operations since client's base version
                    existing_ops = await self.get_operations_since(canvas_id, base_version)

                    # Transform incoming operations against existing ones
                    transformed_operations = await self._transform_operations(operations, existing_ops)

                    # Use the transformed operations
                    operations_to_apply = transformed_operations
                else:
                    # No transformation needed, use original operations
                    operations_to_apply = operations

                # Apply operations to canvas state
                new_state, errors = await self._apply_operations_to_state(state, operations_to_apply)

                if errors:
                    logger.warning(f"Errors applying operations: {errors}")

                # Update version
                new_version = current_version + len(operations)
                new_state["version"] = new_version

                # Save updated state
                success = await self.save_canvas_state(canvas_id, new_state)
                if not success:
                    return None

                # Save operations to history
                await self.save_operations(canvas_id, operations, base_version, new_version)

                # Return result
                return OperationTransform(
                    operations=operations,
                    transformed_operations=transformed_operations,
                    new_version=new_version,
                    needs_transform=needs_transform,
                    conflicts=errors
                )

            except Exception as e:
                logger.error(f"Error applying operations: {e}")
                return None

    async def _transform_operations(
        self,
        client_ops: List[CanvasOperation],
        server_ops: List[Dict[str, Any]]
    ) -> List[CanvasOperation]:
        """Transform client operations against server operations"""
        # This is a simplified implementation
        # In a production system, you'd implement proper OT algorithms

        # For now, just return the original operations
        # In a real implementation, you'd apply transformation rules
        return client_ops

    async def _apply_operations_to_state(
        self,
        state: Dict[str, Any],
        operations: List[CanvasOperation]
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Apply operations to canvas state"""
        new_state = state.copy()
        errors = []

        # Ensure elements dict exists
        if "elements" not in new_state:
            new_state["elements"] = {}

        for op in operations:
            try:
                if op.type.value == "create":
                    # Create a new element
                    element_id = op.target_id
                    new_state["elements"][element_id] = op.properties

                elif op.type.value == "update":
                    # Update an existing element
                    element_id = op.target_id
                    if element_id in new_state["elements"]:
                        # Update properties
                        for key, value in op.properties.items():
                            new_state["elements"][element_id][key] = value
                    else:
                        errors.append({
                            "operation": op.dict(),
                            "error": f"Element {element_id} not found"
                        })

                elif op.type.value == "delete":
                    # Delete an element
                    element_id = op.target_id
                    if element_id in new_state["elements"]:
                        del new_state["elements"][element_id]
                    else:
                        errors.append({
                            "operation": op.dict(),
                            "error": f"Element {element_id} not found"
                        })

                elif op.type.value == "move":
                    # Move an element
                    element_id = op.target_id
                    if element_id in new_state["elements"]:
                        if "position" in op.properties:
                            if "x" in op.properties["position"]:
                                new_state["elements"][element_id]["x"] = op.properties["position"]["x"]
                            if "y" in op.properties["position"]:
                                new_state["elements"][element_id]["y"] = op.properties["position"]["y"]
                    else:
                        errors.append({
                            "operation": op.dict(),
                            "error": f"Element {element_id} not found"
                        })

                # Add handlers for other operation types
                # ...

            except Exception as e:
                errors.append({
                    "operation": op.dict(),
                    "error": str(e)
                })

        return new_state, errors
