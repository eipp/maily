from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from loguru import logger

from ..services.auth_service import get_current_user
from ..models.user import User
from ..db.database import get_db
from sqlalchemy.orm import Session
from ..cache.redis_pubsub import RedisPubSub
from ..services.operational_transform import OperationalTransform

router = APIRouter(prefix="/v1/canvas")

class CollaboratorModel(BaseModel):
    email: str

class CreateCanvasRequest(BaseModel):
    name: str
    campaignId: Optional[str] = None
    initialState: Optional[str] = None
    collaborators: List[str] = Field(default_factory=list)

class CanvasStateUpdate(BaseModel):
    state: str
    version: int

class CanvasOperation(BaseModel):
    id: str
    type: str  # add, update, delete
    data: Dict[str, Any]
    timestamp: Optional[str] = None

class CanvasOperationsRequest(BaseModel):
    operations: List[CanvasOperation]
    baseVersion: int

# Get Redis PubSub instance
pubsub = RedisPubSub()

# Get Operational Transform service
ot_service = OperationalTransform()

@router.post("/create")
async def create_canvas(
    request: CreateCanvasRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new canvas for collaboration"""
    try:
        # Generate a unique canvas ID
        canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"

        # Create canvas record in database
        # db.execute(...) - Implementation depends on your DB schema

        # Notify about new canvas creation
        room_id = f"room_{canvas_id}"
        await pubsub.publish(f"canvas:{room_id}", {
            "type": "canvas_created",
            "canvasId": canvas_id,
            "userId": current_user.id,
            "userName": current_user.name,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Return canvas info with collaboration URL
        return {
            "canvasId": canvas_id,
            "status": "created",
            "collaborationUrl": f"https://app.maily.example.com/canvas/{canvas_id}",
            "websocketRoom": room_id
        }
    except Exception as e:
        logger.error(f"Failed to create canvas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{canvas_id}/state")
async def update_canvas_state(
    canvas_id: str,
    state_update: CanvasStateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update canvas state for persistence"""
    try:
        # Verify canvas exists and user has access
        # Implementation depends on your DB schema

        # Update canvas state in database
        # db.execute(...) - Implementation depends on your DB schema

        # Notify about state update
        room_id = f"room_{canvas_id}"
        await pubsub.publish(f"canvas:{room_id}", {
            "type": "state_persistent_update",
            "canvasId": canvas_id,
            "userId": current_user.id,
            "userName": current_user.name,
            "version": state_update.version + 1,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Return updated state info
        return {
            "status": "updated",
            "version": state_update.version + 1,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to update canvas state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{canvas_id}/state")
async def get_canvas_state(
    canvas_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve canvas state"""
    try:
        # Verify canvas exists and user has access
        # Implementation depends on your DB schema

        # Get canvas state from database
        # Implementation depends on your DB schema

        # Notify about canvas access
        room_id = f"room_{canvas_id}"
        await pubsub.publish(f"canvas:{room_id}", {
            "type": "canvas_accessed",
            "canvasId": canvas_id,
            "userId": current_user.id,
            "userName": current_user.name,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Return canvas state data
        return {
            "canvasId": canvas_id,
            "state": "base64-encoded-canvas-state", # Replace with actual state
            "version": 1, # Replace with actual version
            "lastUpdated": datetime.utcnow().isoformat(),
            "collaborators": [
                {"userId": "user1", "name": "Alice", "lastActive": datetime.utcnow().isoformat()}
            ] # Replace with actual collaborators
        }
    except Exception as e:
        logger.error(f"Failed to get canvas state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{canvas_id}/operations")
async def apply_operations(
    canvas_id: str,
    operations_req: CanvasOperationsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply operations to canvas using operational transforms"""
    try:
        # Get current canvas version from database
        # current_version = ... (implementation depends on your DB schema)
        current_version = 1  # Placeholder

        # Check for concurrent modifications
        if operations_req.baseVersion != current_version:
            # Get server operations that occurred since client's base version
            # server_ops = ... (fetch from database)
            server_ops = []  # Placeholder

            # Transform client operations against server operations
            transformed_ops = ot_service.transform_operations(
                client_ops=[op.dict() for op in operations_req.operations],
                server_ops=server_ops
            )

            # Apply transformed operations
            # ... (implementation depends on your DB schema)

            # Notify about transformed operations
            room_id = f"room_{canvas_id}"
            await pubsub.publish(f"canvas:{room_id}", {
                "type": "operations_applied",
                "canvasId": canvas_id,
                "userId": current_user.id,
                "userName": current_user.name,
                "operations": transformed_ops,
                "version": current_version + 1,
                "timestamp": datetime.utcnow().isoformat()
            })

            return {
                "status": "transformed",
                "operations": transformed_ops,
                "version": current_version + 1
            }
        else:
            # No conflicts, apply operations directly
            # ... (implementation depends on your DB schema)

            # Notify about operations
            room_id = f"room_{canvas_id}"
            client_ops = [op.dict() for op in operations_req.operations]

            # Add timestamps to operations
            current_time = datetime.utcnow().isoformat()
            for op in client_ops:
                op["timestamp"] = current_time

            await pubsub.publish(f"canvas:{room_id}", {
                "type": "operations_applied",
                "canvasId": canvas_id,
                "userId": current_user.id,
                "userName": current_user.name,
                "operations": client_ops,
                "version": current_version + 1,
                "timestamp": current_time
            })

            return {
                "status": "applied",
                "operations": client_ops,
                "version": current_version + 1
            }
    except Exception as e:
        logger.error(f"Failed to apply operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{canvas_id}/operations")
async def get_operations(
    canvas_id: str,
    since_version: int,
    current_user: User = Depends(get_current_user)
):
    """Get operations since a specific version"""
    try:
        # Verify canvas exists and user has access
        # Implementation depends on your DB schema

        # Retrieve operations from database
        # operations = ... (implementation depends on your DB schema)
        # This is a placeholder implementation
        operations = []
        current_version = 1

        return {
            "canvasId": canvas_id,
            "operations": operations,
            "baseVersion": since_version,
            "currentVersion": current_version
        }
    except Exception as e:
        logger.error(f"Failed to get operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
