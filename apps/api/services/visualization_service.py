"""
Visualization Service for Cognitive Canvas

This service provides visualization layers for AI reasoning, performance insights,
and trust verification in the Cognitive Canvas.
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from ..utils.encryption import encrypt_data, decrypt_data
from packages.database.src.redis import get_redis_client
from ..utils.tracing import setup_tracing, trace_function
from ..services.performance_insights_service import get_performance_insights_service
from ..services.trust_verification_service import get_trust_verification_service

# Setup tracing
tracer = setup_tracing("visualization_service")
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
        self.redis = None
        self.performance_service = None
        self.trust_verification_service = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the service with required dependencies"""
        if self.initialized:
            return
            
        self.redis = await get_redis_client()
        self.performance_service = get_performance_insights_service()
        self.trust_verification_service = get_trust_verification_service()
        await self.trust_verification_service.initialize()
        self.initialized = True
        logger.info("Visualization service initialized")
        
    @trace_function(tracer, "get_visualization_layers")
    async def get_visualization_layers(self, canvas_id: str) -> Dict[str, Any]:
        """Get all visualization layers for a canvas"""
        if not self.initialized:
            await self.initialize()
            
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
    
    @trace_function(tracer, "update_ai_reasoning_layer")
    async def update_ai_reasoning_layer(
        self, 
        canvas_id: str, 
        confidence_scores: Dict[str, float],
        reasoning_steps: List[Dict[str, Any]],
        model_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update AI reasoning visualization layer"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Update AI reasoning layer
            if "ai_reasoning" in layers:
                layers["ai_reasoning"]["confidence_scores"] = confidence_scores
                layers["ai_reasoning"]["reasoning_steps"] = reasoning_steps
                layers["ai_reasoning"]["model_info"] = model_info
                layers["ai_reasoning"]["updated_at"] = datetime.utcnow().isoformat()
                
                # Add additional data visualization elements
                reasoning_data = self._process_reasoning_data(reasoning_steps, confidence_scores)
                layers["ai_reasoning"]["data"] = reasoning_data
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            # Emit websocket notification for real-time updates
            await self._notify_layer_update(canvas_id, "ai_reasoning", layers["ai_reasoning"])
            
            return layers["ai_reasoning"]
            
        except Exception as e:
            logger.error(f"Failed to update AI reasoning layer: {e}")
            raise
            
    def _process_reasoning_data(
        self,
        reasoning_steps: List[Dict[str, Any]],
        confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Process reasoning steps into visualization-friendly data"""
        visualization_data = {
            "nodes": [],
            "links": [],
            "confScores": {}
        }
        
        # Create graph structure from reasoning steps
        for i, step in enumerate(reasoning_steps):
            node_id = f"step_{i}"
            
            # Create node
            node = {
                "id": node_id,
                "label": step.get("label", f"Step {i+1}"),
                "type": step.get("type", "reasoning"),
                "content": step.get("content", ""),
                "position": i
            }
            
            visualization_data["nodes"].append(node)
            
            # Create links between steps
            if i > 0:
                link = {
                    "source": f"step_{i-1}",
                    "target": node_id,
                    "value": 1
                }
                visualization_data["links"].append(link)
                
        # Add confidence scores
        visualization_data["confScores"] = confidence_scores
            
        return visualization_data
    
    @trace_function(tracer, "update_performance_layer")
    async def update_performance_layer(
        self, 
        canvas_id: str, 
        metrics: Dict[str, Any] = None,
        historical_data: List[Dict[str, Any]] = None,
        benchmarks: Dict[str, Any] = None,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update performance insights visualization layer"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # If metrics weren't provided but campaign_id is, fetch performance data
            if (not metrics or not historical_data or not benchmarks) and campaign_id:
                performance_data = await self.performance_service.get_email_performance_metrics(
                    canvas_id=canvas_id,
                    campaign_id=campaign_id
                )
                
                metrics = performance_data.get("metrics", {})
                historical_data = performance_data.get("historical_data", [])
                benchmarks = performance_data.get("benchmarks", {})
                
            # Update performance layer
            if "performance" in layers:
                if metrics:
                    layers["performance"]["metrics"] = metrics
                if historical_data:
                    layers["performance"]["historical_data"] = historical_data
                if benchmarks:
                    layers["performance"]["benchmarks"] = benchmarks
                    
                layers["performance"]["updated_at"] = datetime.utcnow().isoformat()
                
                # Process performance data for visualization
                visualization_data = self._process_performance_data(
                    metrics, 
                    historical_data, 
                    benchmarks
                )
                layers["performance"]["data"] = visualization_data
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            # Emit websocket notification for real-time updates
            await self._notify_layer_update(canvas_id, "performance", layers["performance"])
            
            return layers["performance"]
            
        except Exception as e:
            logger.error(f"Failed to update performance layer: {e}")
            raise
            
    def _process_performance_data(
        self,
        metrics: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        benchmarks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process performance metrics into visualization-friendly data"""
        visualization_data = {
            "charts": [],
            "comparisons": [],
            "timeline": []
        }
        
        # Process metric data for charts
        if metrics:
            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and "value" in metric_data:
                    chart_data = {
                        "id": f"metric_{metric_name}",
                        "type": "gauge",
                        "label": metric_name.replace("_", " ").title(),
                        "value": metric_data["value"],
                        "unit": metric_data.get("unit", ""),
                        "benchmark": metric_data.get("benchmark", None),
                        "trend": metric_data.get("trend", "neutral")
                    }
                    visualization_data["charts"].append(chart_data)
        
        # Process benchmark comparisons
        if benchmarks:
            for category, category_data in benchmarks.items():
                for metric_name, benchmark_value in category_data.items():
                    metric_value = metrics.get(metric_name, {}).get("value") if metrics else None
                    if metric_value is not None:
                        comparison = {
                            "id": f"comp_{category}_{metric_name}",
                            "metric": metric_name,
                            "category": category,
                            "actual": metric_value,
                            "benchmark": benchmark_value,
                            "difference": metric_value - benchmark_value,
                            "percentDiff": (metric_value / benchmark_value - 1) * 100 if benchmark_value else 0
                        }
                        visualization_data["comparisons"].append(comparison)
        
        # Process historical data for timeline
        if historical_data:
            # For date-based historical data
            if all("date" in entry for entry in historical_data):
                timeline_data = []
                metrics_set = set()
                
                # Collect all metrics from historical data
                for entry in historical_data:
                    for key, value in entry.items():
                        if key != "date" and isinstance(value, (int, float)):
                            metrics_set.add(key)
                
                # Create timeline series for each metric
                for metric in metrics_set:
                    series = {
                        "id": metric,
                        "name": metric.replace("_", " ").title(),
                        "data": [
                            {"x": entry.get("date", ""), "y": entry.get(metric, 0)}
                            for entry in historical_data
                        ]
                    }
                    timeline_data.append(series)
                
                visualization_data["timeline"] = timeline_data
                
        return visualization_data
    
    @trace_function(tracer, "update_trust_verification_layer")
    async def update_trust_verification_layer(
        self, 
        canvas_id: str, 
        verification_status: Optional[str] = None,
        certificate_data: Optional[Dict[str, Any]] = None,
        blockchain_info: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update trust verification visualization layer"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # If content is provided, verify it and get verification data
            if content and not certificate_data and not blockchain_info:
                # Use the trust verification service to verify content
                verification_data = await self.trust_verification_service.verify_canvas_content(
                    canvas_id=canvas_id,
                    content=content,
                    user_id="system_visualization"  # System-initiated verification
                )
                
                verification_status = verification_data.get("status", {}).get("status", "unverified")
                certificate_data = verification_data.get("certificate", None)
                blockchain_info = verification_data.get("blockchain", None)
            
            # Update trust verification layer
            if "trust_verification" in layers:
                if verification_status:
                    layers["trust_verification"]["verification_status"] = verification_status
                if certificate_data:
                    layers["trust_verification"]["certificate_data"] = certificate_data
                if blockchain_info:
                    layers["trust_verification"]["blockchain_info"] = blockchain_info
                
                layers["trust_verification"]["updated_at"] = datetime.utcnow().isoformat()
                
                # Process verification data for visualization
                visualization_data = self._process_verification_data(
                    verification_status, 
                    certificate_data, 
                    blockchain_info
                )
                layers["trust_verification"]["data"] = visualization_data
            
            # Store updated layers
            layers_key = f"canvas:{canvas_id}:visualization_layers"
            await self.redis.set(
                layers_key, 
                json.dumps(layers),
                expire=86400 * 30  # 30 days
            )
            
            # Emit websocket notification for real-time updates
            await self._notify_layer_update(canvas_id, "trust_verification", layers["trust_verification"])
            
            return layers["trust_verification"]
            
        except Exception as e:
            logger.error(f"Failed to update trust verification layer: {e}")
            raise
            
    def _process_verification_data(
        self,
        verification_status: str,
        certificate_data: Optional[Dict[str, Any]],
        blockchain_info: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process verification data into visualization-friendly format"""
        visualization_data = {
            "verificationStatus": verification_status,
            "certificateVisual": None,
            "blockchainVisual": None,
            "timeline": []
        }
        
        # Process certificate data
        if certificate_data:
            certificate_visual = {
                "id": certificate_data.get("id", ""),
                "issuer": certificate_data.get("issuer", ""),
                "issuedAt": certificate_data.get("issued_at", ""),
                "contentHash": certificate_data.get("content_hash", "").strip()[:15] + "...",
                "fullContentHash": certificate_data.get("content_hash", ""),
                "signatureValid": bool(certificate_data.get("signature", "")),
                "elements": [
                    {"label": "Certificate ID", "value": certificate_data.get("id", "")},
                    {"label": "Issuer", "value": certificate_data.get("issuer", "")},
                    {"label": "Subject", "value": certificate_data.get("subject", "")},
                    {"label": "Issued Date", "value": certificate_data.get("issued_at", "")},
                    {"label": "Content Hash", "value": certificate_data.get("content_hash", "").strip()[:15] + "..."},
                    {"label": "Signature", "value": certificate_data.get("signature", "").strip()[:15] + "..."}
                ]
            }
            visualization_data["certificateVisual"] = certificate_visual
        
        # Process blockchain info
        if blockchain_info:
            blockchain_visual = {
                "transactionId": blockchain_info.get("transaction_id", "").strip()[:15] + "...",
                "fullTransactionId": blockchain_info.get("transaction_id", ""),
                "blockNumber": blockchain_info.get("block_number", ""),
                "timestamp": blockchain_info.get("timestamp", ""),
                "network": blockchain_info.get("network", ""),
                "contractAddress": blockchain_info.get("contract_address", "").strip()[:15] + "...",
                "fullContractAddress": blockchain_info.get("contract_address", ""),
                "elements": [
                    {"label": "Transaction ID", "value": blockchain_info.get("transaction_id", "").strip()[:15] + "..."},
                    {"label": "Block", "value": blockchain_info.get("block_number", "")},
                    {"label": "Timestamp", "value": blockchain_info.get("timestamp", "")},
                    {"label": "Network", "value": blockchain_info.get("network", "")},
                    {"label": "Contract", "value": blockchain_info.get("contract_address", "").strip()[:10] + "..."}
                ]
            }
            visualization_data["blockchainVisual"] = blockchain_visual
            
        # Create verification timeline
        timeline = []
        
        # Add certificate issuance to timeline
        if certificate_data and certificate_data.get("issued_at"):
            timeline.append({
                "id": "certificate_issued",
                "label": "Certificate Issued",
                "timestamp": certificate_data.get("issued_at", ""),
                "type": "certificate"
            })
        
        # Add blockchain verification to timeline
        if blockchain_info and blockchain_info.get("timestamp"):
            timeline.append({
                "id": "blockchain_verified",
                "label": "Blockchain Verification",
                "timestamp": blockchain_info.get("timestamp", ""),
                "type": "blockchain",
                "blockNumber": blockchain_info.get("block_number", "")
            })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x.get("timestamp", ""))
        visualization_data["timeline"] = timeline
            
        return visualization_data
    
    @trace_function(tracer, "update_layer_visibility")
    async def update_layer_visibility(
        self, 
        canvas_id: str, 
        layer_id: str,
        visible: bool,
        opacity: Optional[float] = None
    ) -> Dict[str, Any]:
        """Update layer visibility and opacity"""
        if not self.initialized:
            await self.initialize()
            
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
            
            # Emit websocket notification for real-time updates
            await self._notify_layer_update(canvas_id, layer_id, layers[layer_id] if layer_id in layers else None, "visibility_update")
            
            return layers[layer_id] if layer_id in layers else {}
            
        except Exception as e:
            logger.error(f"Failed to update layer visibility: {e}")
            raise
    
    async def _notify_layer_update(
        self, 
        canvas_id: str, 
        layer_id: str, 
        layer_data: Dict[str, Any],
        update_type: str = "layer_update"
    ):
        """Send WebSocket notification about layer updates"""
        try:
            # Import WebSocket service
            from ..services.websocket_service import get_connection_manager
            from ..utils.tracing import create_websocket_span
            
            with create_websocket_span("layer_update", room_id=f"room_{canvas_id}", message_type=update_type):
                # Get connection manager
                connection_manager = get_connection_manager()
                
                # Create room ID from canvas ID
                room_id = f"room_{canvas_id}"
                
                # Create notification message
                message = {
                    "type": update_type,
                    "roomId": room_id,
                    "layerId": layer_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "payload": {
                        "layerId": layer_id,
                        "visibility": layer_data.get("visible", True) if layer_data else True,
                        "opacity": layer_data.get("opacity", 1.0) if layer_data else 1.0,
                        "updateType": update_type,
                        "layer": layer_data
                    }
                }
                
                # Use standardized WebSocket message
                from ..services.websocket_service import MessageType, WebSocketMessage
                
                ws_message = WebSocketMessage(
                    type=MessageType.CANVAS_UPDATE,
                    data=message,
                    sender="visualization_service"
                )
                
                # Broadcast to all clients in room
                await connection_manager.broadcast(ws_message, room_id)
                
                # For backwards compatibility, also publish via Redis PubSub
                from ..cache.redis_pubsub import RedisPubSub
                pubsub = RedisPubSub()
                channel = f"canvas:{room_id}"
                await pubsub.publish(channel, message)
                
        except Exception as e:
            logger.error(f"Failed to notify about layer update: {e}")
    
    @trace_function(tracer, "sync_visualization_with_performance")
    async def sync_visualization_with_performance(self, canvas_id: str, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """Synchronize visualization layer with latest performance data"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get performance data
            performance_data = await self.performance_service.get_email_performance_metrics(
                canvas_id=canvas_id,
                campaign_id=campaign_id
            )
            
            # Update visualization layer
            updated_layer = await self.update_performance_layer(
                canvas_id=canvas_id,
                metrics=performance_data.get("metrics", {}),
                historical_data=performance_data.get("historical_data", []),
                benchmarks=performance_data.get("benchmarks", {})
            )
            
            return updated_layer
            
        except Exception as e:
            logger.error(f"Failed to sync visualization with performance: {e}")
            raise
    
    @trace_function(tracer, "sync_visualization_with_verification")
    async def sync_visualization_with_verification(self, canvas_id: str, content: Optional[str] = None) -> Dict[str, Any]:
        """Synchronize visualization layer with latest verification data"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # If content is provided, verify it
            if content:
                verification_data = await self.trust_verification_service.verify_canvas_content(
                    canvas_id=canvas_id,
                    content=content,
                    user_id="system_visualization"
                )
                
                # Update visualization layer
                updated_layer = await self.update_trust_verification_layer(
                    canvas_id=canvas_id,
                    verification_status=verification_data.get("status", {}).get("status", "unverified"),
                    certificate_data=verification_data.get("certificate", None),
                    blockchain_info=verification_data.get("blockchain", None)
                )
            else:
                # Get latest verification data
                verification_data = await self.trust_verification_service.get_verification_data(canvas_id)
                
                # Update visualization layer
                updated_layer = await self.update_trust_verification_layer(
                    canvas_id=canvas_id,
                    verification_status=verification_data.get("status", {}).get("status", "unverified"),
                    certificate_data=verification_data.get("certificate", None),
                    blockchain_info=verification_data.get("blockchain", None)
                )
            
            return updated_layer
            
        except Exception as e:
            logger.error(f"Failed to sync visualization with verification: {e}")
            raise
            
    @trace_function(tracer, "get_trust_verification_badge")
    async def get_trust_verification_badge(self, canvas_id: str) -> Dict[str, Any]:
        """Get trust verification badge for a canvas"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Get trust verification layer
            trust_layer = layers.get("trust_verification", {})
            verification_status = trust_layer.get("verification_status", "unverified")
            
            # If not verified, return empty badge
            if verification_status != "verified":
                return {
                    "status": "unverified",
                    "badge_url": None,
                    "qr_code": None,
                    "verification_url": None
                }
                
            # Get badge data from verification layer
            certificate_data = trust_layer.get("certificate_data", {})
            blockchain_info = trust_layer.get("blockchain_info", {})
            
            # Get or generate QR code for verification
            qr_code = await self.trust_verification_service.get_verification_qr_code(canvas_id)
            
            # Build verification URL
            verification_url = None
            if certificate_data and certificate_data.get("id"):
                verification_url = f"{self.trust_verification_service.verification_base_url}/verify/{certificate_data.get('id')}"
            
            # Build badge data
            badge_data = {
                "status": verification_status,
                "badge_url": qr_code,
                "qr_code": qr_code,
                "verification_url": verification_url,
                "certificate_id": certificate_data.get("id") if certificate_data else None,
                "issuer": certificate_data.get("issuer") if certificate_data else None,
                "issued_at": certificate_data.get("issued_at") if certificate_data else None,
                "transaction_id": blockchain_info.get("transaction_id") if blockchain_info else None,
                "blockchain": blockchain_info.get("network") if blockchain_info else None
            }
            
            return badge_data
            
        except Exception as e:
            logger.error(f"Failed to get trust verification badge: {e}")
            raise
            
    @trace_function(tracer, "generate_trust_verification_overlay")
    async def generate_trust_verification_overlay(self, canvas_id: str) -> Dict[str, Any]:
        """Generate trust verification overlay for the canvas"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Get current layers
            layers = await self.get_visualization_layers(canvas_id)
            
            # Get trust verification layer
            trust_layer = layers.get("trust_verification", {})
            verification_status = trust_layer.get("verification_status", "unverified")
            
            # If not verified, return empty overlay
            if verification_status != "verified":
                return {
                    "status": "unverified",
                    "overlay": None
                }
                
            # Get certificate and blockchain data
            certificate_data = trust_layer.get("certificate_data", {})
            blockchain_info = trust_layer.get("blockchain_info", {})
            
            # Create overlay elements
            overlay = {
                "border": {
                    "color": "rgba(0, 160, 0, 0.5)",
                    "width": 4,
                    "style": "solid"
                },
                "badge": {
                    "position": "top-right",
                    "text": "Verified Content",
                    "certificate_id": certificate_data.get("id", "").strip()[:10] + "..." if certificate_data else "",
                    "timestamp": certificate_data.get("issued_at") if certificate_data else "",
                    "issuer": certificate_data.get("issuer") if certificate_data else ""
                },
                "watermark": {
                    "text": "Blockchain Verified",
                    "opacity": 0.05,
                    "angle": -30,
                    "color": "rgba(0, 120, 0, 0.1)"
                },
                "footer": {
                    "text": f"Verified on {blockchain_info.get('network', 'Blockchain') if blockchain_info else 'Blockchain'} • TX: {blockchain_info.get('transaction_id', '').strip()[:10] + '...' if blockchain_info else ''}",
                    "position": "bottom",
                    "color": "rgba(0, 100, 0, 0.7)"
                }
            }
            
            return {
                "status": verification_status,
                "overlay": overlay
            }
            
        except Exception as e:
            logger.error(f"Failed to generate trust verification overlay: {e}")
            raise
            
    @trace_function(tracer, "verify_and_visualize_canvas")
    async def verify_and_visualize_canvas(self, canvas_id: str, content: str) -> Dict[str, Any]:
        """Verify canvas content and prepare visualization in one operation"""
        if not self.initialized:
            await self.initialize()
            
        try:
            # Verify content and update trust verification layer
            trust_layer = await self.update_trust_verification_layer(
                canvas_id=canvas_id,
                content=content
            )
            
            # Get verification status
            verification_status = trust_layer.get("verification_status", "unverified")
            
            # Generate badge and overlay if verified
            badge_data = {}
            overlay_data = {}
            if verification_status == "verified":
                badge_data = await self.get_trust_verification_badge(canvas_id)
                overlay_data = await self.generate_trust_verification_overlay(canvas_id)
            
            # Return combined verification data
            return {
                "status": verification_status,
                "layer": trust_layer,
                "badge": badge_data.get("badge_url"),
                "qr_code": badge_data.get("qr_code"),
                "verification_url": badge_data.get("verification_url"),
                "overlay": overlay_data.get("overlay")
            }
            
        except Exception as e:
            logger.error(f"Failed to verify and visualize canvas: {e}")
            raise

# Singleton instance
_instance = None

def get_visualization_service():
    """Get singleton instance of VisualizationService"""
    global _instance
    if _instance is None:
        _instance = VisualizationService()
    return _instance
