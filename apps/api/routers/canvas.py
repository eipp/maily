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
from packages.database.src.redis import RedisPubSub, get_redis_pubsub
from ..services.operational_transform import OperationalTransform
from ..services.visualization_service import get_visualization_service
from ..services.performance_insights_service import get_performance_insights_service
from ..services.trust_verification_service import get_trust_verification_service

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

# Get Operational Transform service
ot_service = OperationalTransform()

# PubSub instance will be initialized in each function
pubsub = None

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
        # Get Redis PubSub instance
        pubsub = await get_redis_pubsub()
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
        # Get Redis PubSub instance
        pubsub = await get_redis_pubsub()
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
        # Get Redis PubSub instance
        pubsub = await get_redis_pubsub()
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
            # Get Redis PubSub instance
            pubsub = await get_redis_pubsub()
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

            # Get Redis PubSub instance
            pubsub = await get_redis_pubsub()
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

# Visualization Layer Endpoints

class AIReasoningUpdateRequest(BaseModel):
    """Request model for updating AI reasoning layer"""
    confidence_scores: Dict[str, float]
    reasoning_steps: List[Dict[str, Any]]
    model_info: Dict[str, Any]

class PerformanceUpdateRequest(BaseModel):
    """Request model for updating performance layer"""
    metrics: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    benchmarks: Dict[str, Any]

class TrustVerificationUpdateRequest(BaseModel):
    """Request model for updating trust verification layer"""
    verification_status: str
    certificate_data: Optional[Dict[str, Any]] = None
    blockchain_info: Optional[Dict[str, Any]] = None

class LayerVisibilityRequest(BaseModel):
    """Request model for updating layer visibility"""
    visible: bool
    opacity: Optional[float] = None

@router.get("/{canvas_id}/visualization/layers")
async def get_visualization_layers(
    canvas_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all visualization layers for a canvas"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Get layers
        layers = await visualization_service.get_visualization_layers(canvas_id)
        
        return layers
    except Exception as e:
        logger.error(f"Failed to get visualization layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{canvas_id}/visualization/layers/ai_reasoning")
async def update_ai_reasoning_layer(
    canvas_id: str,
    request: AIReasoningUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update AI reasoning visualization layer"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
        
        # Update layer
        updated_layer = await visualization_service.update_ai_reasoning_layer(
            canvas_id=canvas_id,
            confidence_scores=request.confidence_scores,
            reasoning_steps=request.reasoning_steps,
            model_info=request.model_info
        )
        
        return updated_layer
    except Exception as e:
        logger.error(f"Failed to update AI reasoning layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{canvas_id}/visualization/layers/performance")
async def update_performance_layer(
    canvas_id: str,
    request: PerformanceUpdateRequest,
    campaign_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update performance insights visualization layer"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
        
        # Update layer
        updated_layer = await visualization_service.update_performance_layer(
            canvas_id=canvas_id,
            metrics=request.metrics,
            historical_data=request.historical_data,
            benchmarks=request.benchmarks,
            campaign_id=campaign_id
        )
        
        return updated_layer
    except Exception as e:
        logger.error(f"Failed to update performance layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{canvas_id}/visualization/layers/trust_verification")
async def update_trust_verification_layer(
    canvas_id: str,
    request: TrustVerificationUpdateRequest = Body(...),
    content: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Update trust verification visualization layer"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
        
        # Update layer
        updated_layer = await visualization_service.update_trust_verification_layer(
            canvas_id=canvas_id,
            verification_status=request.verification_status,
            certificate_data=request.certificate_data,
            blockchain_info=request.blockchain_info,
            content=content
        )
        
        return updated_layer
    except Exception as e:
        logger.error(f"Failed to update trust verification layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{canvas_id}/visualization/layers/{layer_id}/visibility")
async def update_layer_visibility(
    canvas_id: str,
    layer_id: str,
    request: LayerVisibilityRequest,
    current_user: User = Depends(get_current_user)
):
    """Update layer visibility and opacity"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
        
        # Update layer visibility
        updated_layer = await visualization_service.update_layer_visibility(
            canvas_id=canvas_id,
            layer_id=layer_id,
            visible=request.visible,
            opacity=request.opacity
        )
        
        return updated_layer
    except Exception as e:
        logger.error(f"Failed to update layer visibility: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Performance Insights Endpoints

@router.get("/{canvas_id}/performance/metrics")
async def get_performance_metrics(
    canvas_id: str,
    campaign_id: Optional[str] = None,
    sync_visualization: Optional[bool] = False,
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a canvas or campaign"""
    try:
        # Get performance insights service
        performance_service = get_performance_insights_service()
        
        # Get metrics
        metrics = await performance_service.get_email_performance_metrics(
            canvas_id=canvas_id,
            campaign_id=campaign_id
        )
        
        # Optionally sync with visualization layer
        if sync_visualization:
            visualization_service = get_visualization_service()
            
            # Initialize service if needed
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
                
            await visualization_service.sync_visualization_with_performance(
                canvas_id=canvas_id,
                campaign_id=campaign_id
            )
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Trust Verification Endpoints

class VerifyContentRequest(BaseModel):
    """Request model for verifying content"""
    content: str

@router.post("/{canvas_id}/verify")
async def verify_canvas_content(
    canvas_id: str,
    request: VerifyContentRequest,
    sync_visualization: Optional[bool] = True,
    current_user: User = Depends(get_current_user)
):
    """Verify canvas content and store on blockchain"""
    try:
        # Get trust verification service
        verification_service = get_trust_verification_service()
        
        # Initialize service if needed
        if not hasattr(verification_service, "redis") or verification_service.redis is None:
            await verification_service.initialize()
        
        # Verify content
        verification_data = await verification_service.verify_canvas_content(
            canvas_id=canvas_id,
            content=request.content,
            user_id=current_user.id
        )
        
        # Optionally sync with visualization layer
        if sync_visualization:
            visualization_service = get_visualization_service()
            
            # Initialize service if needed
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
                
            await visualization_service.sync_visualization_with_verification(
                canvas_id=canvas_id
            )
        
        return verification_data
    except Exception as e:
        logger.error(f"Failed to verify canvas content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{canvas_id}/verification")
async def get_verification_data(
    canvas_id: str,
    sync_visualization: Optional[bool] = False,
    current_user: User = Depends(get_current_user)
):
    """Get verification data for a canvas"""
    try:
        # Get trust verification service
        verification_service = get_trust_verification_service()
        
        # Initialize service if needed
        if not hasattr(verification_service, "redis") or verification_service.redis is None:
            await verification_service.initialize()
        
        # Get verification data
        verification_data = await verification_service.get_verification_data(canvas_id)
        
        # Optionally sync with visualization layer
        if sync_visualization:
            visualization_service = get_visualization_service()
            
            # Initialize service if needed
            if not getattr(visualization_service, "initialized", False):
                await visualization_service.initialize()
                
            await visualization_service.sync_visualization_with_verification(
                canvas_id=canvas_id
            )
        
        return verification_data
    except Exception as e:
        logger.error(f"Failed to get verification data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{canvas_id}/verification/badge")
async def get_verification_badge(
    canvas_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get verification badge for embedding in emails"""
    try:
        # Get trust verification service
        verification_service = get_trust_verification_service()
        
        # Initialize service if needed
        if not hasattr(verification_service, "redis") or verification_service.redis is None:
            await verification_service.initialize()
        
        # Get verification badge
        badge = await verification_service.generate_verification_badge(canvas_id)
        
        return badge
    except Exception as e:
        logger.error(f"Failed to get verification badge: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
# New endpoints for visualization layer synchronization

@router.post("/{canvas_id}/visualization/sync-performance")
async def sync_performance_visualization(
    canvas_id: str,
    campaign_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Synchronize performance visualization layer with latest data"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
            
        # Sync visualization with performance data
        updated_layer = await visualization_service.sync_visualization_with_performance(
            canvas_id=canvas_id,
            campaign_id=campaign_id
        )
        
        return {
            "status": "success",
            "message": "Performance visualization layer synchronized",
            "layer": updated_layer
        }
    except Exception as e:
        logger.error(f"Failed to sync performance visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{canvas_id}/visualization/sync-verification")
async def sync_verification_visualization(
    canvas_id: str,
    content: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Synchronize trust verification visualization layer with latest data"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
            
        # Sync visualization with verification data
        updated_layer = await visualization_service.sync_visualization_with_verification(
            canvas_id=canvas_id,
            content=content
        )
        
        return {
            "status": "success",
            "message": "Trust verification visualization layer synchronized",
            "layer": updated_layer
        }
    except Exception as e:
        logger.error(f"Failed to sync verification visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.post("/{canvas_id}/visualization/verify-and-visualize")
async def verify_and_visualize_canvas(
    canvas_id: str,
    request: VerifyContentRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify canvas content and prepare visualization in one operation"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
            
        # Verify and visualize canvas in one operation
        result = await visualization_service.verify_and_visualize_canvas(
            canvas_id=canvas_id,
            content=request.content
        )
        
        # Notify about verification via websockets
        room_id = f"room_{canvas_id}"
        # Get Redis PubSub instance
        pubsub = await get_redis_pubsub()
        await pubsub.publish(f"canvas:{room_id}", {
            "type": "content_verified",
            "canvasId": canvas_id,
            "userId": current_user.id,
            "userName": current_user.name,
            "status": result["status"],
            "badge": result.get("badge"),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return result
    except Exception as e:
        logger.error(f"Failed to verify and visualize canvas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/{canvas_id}/visualization/trust-overlay")
async def get_trust_verification_overlay(
    canvas_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate trust verification overlay for the canvas"""
    try:
        # Get visualization service
        visualization_service = get_visualization_service()
        
        # Initialize service if needed
        if not getattr(visualization_service, "initialized", False):
            await visualization_service.initialize()
            
        # Generate trust verification overlay
        overlay = await visualization_service.generate_trust_verification_overlay(canvas_id)
        
        return overlay
    except Exception as e:
        logger.error(f"Failed to generate trust verification overlay: {e}")
        raise HTTPException(status_code=500, detail=str(e))
