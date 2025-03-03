"""
Visualization Service for Cognitive Canvas

This service provides visualization layers for AI reasoning, performance insights,
and trust verification in the Cognitive Canvas.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from ..utils.encryption import encrypt_data, decrypt_data
from ..cache.redis_client import get_redis_client

logger = logging.getLogger("api.services.visualization")

class VisualizationLayer(BaseModel):
    """Base model for visualization layers"""
    id: str
    name: str
    type: str
    data: Dict[str, Any]
    opacity: float = 1.0
    visible: bool = True
    created_at: datetime
    updated_at: datetime
    
class AIReasoningLayer(VisualizationLayer):
    """AI reasoning visualization layer"""
    confidence_scores: Dict[str, float]
    reasoning_steps: List[Dict[str, Any]]
    model_info: Dict[str, Any]
    
class PerformanceLayer(VisualizationLayer):
    """Performance insights visualization layer"""
    metrics: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    benchmarks: Dict[str, Any]
    
class TrustVerificationLayer(VisualizationLayer):
    """Trust verification visualization layer"""
    verification_status: str
    certificate_data: Optional[Dict[str, Any]] = None
    blockchain_info: Optional[Dict[str, Any]] = None
    
class VisualizationService:
    """Service for managing visualization layers"""
    
    def __init__(self):
        self.redis = get_redis_client()
        
    async def get_visualization_layers(self, canvas_id: str) -> Dict[str, Any]:
        """Get all visualization layers for a canvas"""
        try:
            # Get layers from Redis
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            layers_data = await self.redis.get(layers_key)
            
            if not layers_data:
                # Initialize default layers if not exists
                default_layers = {
                    "ai_reasoning": {
                        "id": "ai_reasoning",
                        "name": "AI Reasoning",
                        "type": "ai_reasoning",
                        "data": {},
                        "opacity": 0.8,
                        "visible": True,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "confidence_scores": {},
                        "reasoning_steps": [],
                        "model_info": {}
                    },
                    "performance": {
                        "id": "performance",
                        "name": "Performance Insights",
                        "type": "performance",
                        "data": {},
                        "opacity": 0.7,
                        "visible": False,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "metrics": {},
                        "historical_data": [],
                        "benchmarks": {}
                    },
                    "trust_verification": {
                        "id": "trust_verification",
                        "name": "Trust Verification",
                        "type": "trust_verification",
                        "data": {},
                        "opacity": 0.9,
                        "visible": False,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                        "verification_status": "unverified",
                        "certificate_data": None,
                        "blockchain_info": None
                    }
                }
                
                # Store default layers
                await self.redis.set(
                    layers_key, 
                    json.dumps(default_layers),
                    expire=86400 * 30  # 30 days
                )
                
                return default_layers
            
            # Parse layers data
            return json.loads(layers_data)
            
        except Exception as e:
            logger.error(f"Failed to get visualization layers: {e}")
            # Return empty layers on error
            return {}
    
    async def update_ai_reasoning_layer(
        self, 
        canvas_id: str, 
        confidence_scores: Dict[str, float],
        reasoning_steps: List[Dict[str, Any]],
        model_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update AI reasoning visualization layer"""
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Update AI reasoning layer
            if "ai_reasoning" in layers:
                layers["ai_reasoning"]["confidence_scores"] = confidence_scores
                layers["ai_reasoning"]["reasoning_steps"] = reasoning_steps
                layers["ai_reasoning"]["model_info"] = model_info
                layers["ai_reasoning"]["updated_at"] = datetime.utcnow().isoformat()
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            return layers["ai_reasoning"]
            
        except Exception as e:
            logger.error(f"Failed to update AI reasoning layer: {e}")
            raise
    
    async def update_performance_layer(
        self, 
        canvas_id: str, 
        metrics: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update performance insights visualization layer"""
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Update performance layer
            if "performance" in layers:
                layers["performance"]["metrics"] = metrics
                layers["performance"]["historical_data"] = historical_data
                layers["performance"]["benchmarks"] = benchmarks
                layers["performance"]["updated_at"] = datetime.utcnow().isoformat()
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            return layers["performance"]
            
        except Exception as e:
            logger.error(f"Failed to update performance layer: {e}")
            raise
    
    async def update_trust_verification_layer(
        self, 
        canvas_id: str, 
        verification_status: str,
        certificate_data: Optional[Dict[str, Any]] = None,
        blockchain_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update trust verification visualization layer"""
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Update trust verification layer
            if "trust_verification" in layers:
                layers["trust_verification"]["verification_status"] = verification_status
                layers["trust_verification"]["certificate_data"] = certificate_data
                layers["trust_verification"]["blockchain_info"] = blockchain_info
                layers["trust_verification"]["updated_at"] = datetime.utcnow().isoformat()
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            return layers["trust_verification"]
            
        except Exception as e:
            logger.error(f"Failed to update trust verification layer: {e}")
            raise
    
    async def update_layer_visibility(
        self, 
        canvas_id: str, 
        layer_id: str,
        visible: bool,
        opacity: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update layer visibility and opacity"""
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Update layer visibility
            if layer_id in layers:
                layers[layer_id]["visible"] = visible
                if opacity is not None:
                    layers[layer_id]["opacity"] = max(0.0, min(1.0, opacity))
                layers[layer_id]["updated_at"] = datetime.utcnow().isoformat()
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            return layers[layer_id] if layer_id in layers else {}
            
        except Exception as e:
            logger.error(f"Failed to update layer visibility: {e}")
            raise

# Singleton instance
_instance = None

def get_visualization_service():
    """Get singleton instance of VisualizationService"""
    global _instance
    if _instance is None:
        _instance = VisualizationService()
    return _instance
