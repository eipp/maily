"""
Cognitive Canvas Service

This service provides an interactive email design tool with visualization layers for AI reasoning,
performance insights, and trust verification.
"""

import logging
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..utils.redis_client import get_redis_client
from ..utils.llm_client import get_llm_client
from ..utils.database import db_create_canvas, db_get_canvas, db_update_canvas, db_delete_canvas, db_list_canvases

logger = logging.getLogger("ai_service.services.cognitive_canvas")

# Constants
CANVAS_KEY_PREFIX = "cognitive_canvas:"
VISUALIZATION_LAYERS = ["design", "ai_reasoning", "performance", "trust"]

class CognitiveCanvas:
    """Service for interactive email design with visualization layers"""
    
    def __init__(self):
        self.redis = get_redis_client()
        self.llm_client = get_llm_client()
    
    async def create_canvas(
        self,
        name: str,
        description: Optional[str] = None,
        template_id: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Create a new cognitive canvas"""
        try:
            # Generate canvas ID
            canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"
            
            # Create canvas object
            canvas = {
                "id": canvas_id,
                "name": name,
                "description": description or f"Cognitive Canvas: {name}",
                "template_id": template_id,
                "content": content or {},
                "metadata": metadata or {},
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "version": 1,
                "status": "draft",
                "visualization_layers": {
                    "design": {"enabled": True, "data": {}},
                    "ai_reasoning": {"enabled": True, "data": {}},
                    "performance": {"enabled": True, "data": {}},
                    "trust": {"enabled": True, "data": {}}
                },
                "collaborators": [],
                "history": []
            }
            
            # Store canvas in Redis for fast access
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Store canvas in database for persistence
            await db_create_canvas(canvas)
            
            # Initialize visualization layers
            if content:
                await self._initialize_visualization_layers(canvas_id, content)
            
            return canvas_id
            
        except Exception as e:
            logger.error(f"Failed to create canvas: {e}")
            raise
    
    async def get_canvas(self, canvas_id: str) -> Optional[Dict[str, Any]]:
        """Get a cognitive canvas by ID"""
        try:
            # Try to get canvas from Redis first
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            canvas_data = await self.redis.get(canvas_key)
            
            if canvas_data:
                return json.loads(canvas_data)
            
            # If not in Redis, get from database
            canvas = await db_get_canvas(canvas_id)
            
            if canvas:
                # Cache in Redis for future requests
                await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            return canvas
            
        except Exception as e:
            logger.error(f"Failed to get canvas: {e}")
            return None
    
    async def update_canvas(
        self,
        canvas_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update a cognitive canvas"""
        try:
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas:
                return False
            
            # Create a new version if content is being updated
            if "content" in updates:
                # Save current state to history
                if "history" not in canvas:
                    canvas["history"] = []
                
                canvas["history"].append({
                    "version": canvas["version"],
                    "content": canvas["content"],
                    "updated_at": canvas["updated_at"],
                    "visualization_layers": canvas["visualization_layers"]
                })
                
                # Increment version
                canvas["version"] += 1
                
                # Update visualization layers
                await self._update_visualization_layers(canvas_id, updates["content"])
            
            # Update canvas fields
            for key, value in updates.items():
                if key != "id" and key != "created_at" and key != "history" and key != "visualization_layers":
                    canvas[key] = value
            
            # Update timestamps
            canvas["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update canvas: {e}")
            return False
    
    async def delete_canvas(self, canvas_id: str) -> bool:
        """Delete a cognitive canvas"""
        try:
            # Delete from Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.delete(canvas_key)
            
            # Delete from database
            success = await db_delete_canvas(canvas_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete canvas: {e}")
            return False
    
    async def list_canvases(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List cognitive canvases"""
        try:
            # Get canvases from database
            canvases = await db_list_canvases(user_id, status, limit, offset)
            
            # Cache in Redis for future requests
            for canvas in canvases:
                canvas_key = f"{CANVAS_KEY_PREFIX}{canvas['id']}"
                await self.redis.set(canvas_key, json.dumps(canvas), ex=3600)  # 1 hour cache
            
            return canvases
            
        except Exception as e:
            logger.error(f"Failed to list canvases: {e}")
            return []
    
    async def toggle_visualization_layer(
        self,
        canvas_id: str,
        layer: str,
        enabled: bool
    ) -> bool:
        """Toggle a visualization layer on/off"""
        try:
            if layer not in VISUALIZATION_LAYERS:
                raise ValueError(f"Invalid visualization layer: {layer}")
            
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas:
                return False
            
            # Update layer status
            canvas["visualization_layers"][layer]["enabled"] = enabled
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to toggle visualization layer: {e}")
            return False
    
    async def get_visualization_layer(
        self,
        canvas_id: str,
        layer: str
    ) -> Optional[Dict[str, Any]]:
        """Get data for a specific visualization layer"""
        try:
            if layer not in VISUALIZATION_LAYERS:
                raise ValueError(f"Invalid visualization layer: {layer}")
            
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas or "visualization_layers" not in canvas:
                return None
            
            # Return layer data
            return canvas["visualization_layers"].get(layer)
            
        except Exception as e:
            logger.error(f"Failed to get visualization layer: {e}")
            return None
    
    async def add_collaborator(
        self,
        canvas_id: str,
        user_id: str,
        role: str = "viewer"
    ) -> bool:
        """Add a collaborator to the canvas"""
        try:
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas:
                return False
            
            # Check if collaborator already exists
            for collab in canvas.get("collaborators", []):
                if collab["user_id"] == user_id:
                    collab["role"] = role
                    collab["updated_at"] = datetime.utcnow().isoformat()
                    break
            else:
                # Add new collaborator
                if "collaborators" not in canvas:
                    canvas["collaborators"] = []
                
                canvas["collaborators"].append({
                    "user_id": user_id,
                    "role": role,
                    "added_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                })
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add collaborator: {e}")
            return False
    
    async def remove_collaborator(
        self,
        canvas_id: str,
        user_id: str
    ) -> bool:
        """Remove a collaborator from the canvas"""
        try:
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas or "collaborators" not in canvas:
                return False
            
            # Remove collaborator
            canvas["collaborators"] = [c for c in canvas["collaborators"] if c["user_id"] != user_id]
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove collaborator: {e}")
            return False
    
    async def _initialize_visualization_layers(
        self,
        canvas_id: str,
        content: Dict[str, Any]
    ) -> None:
        """Initialize visualization layers for a new canvas"""
        try:
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas:
                return
            
            # Initialize design layer
            design_layer = await self._generate_design_layer(content)
            canvas["visualization_layers"]["design"]["data"] = design_layer
            
            # Initialize AI reasoning layer
            reasoning_layer = await self._generate_reasoning_layer(content)
            canvas["visualization_layers"]["ai_reasoning"]["data"] = reasoning_layer
            
            # Initialize performance layer
            performance_layer = await self._generate_performance_layer(content)
            canvas["visualization_layers"]["performance"]["data"] = performance_layer
            
            # Initialize trust layer
            trust_layer = await self._generate_trust_layer(content)
            canvas["visualization_layers"]["trust"]["data"] = trust_layer
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
        except Exception as e:
            logger.error(f"Failed to initialize visualization layers: {e}")
    
    async def _update_visualization_layers(
        self,
        canvas_id: str,
        content: Dict[str, Any]
    ) -> None:
        """Update visualization layers when content changes"""
        try:
            # Get current canvas
            canvas = await self.get_canvas(canvas_id)
            
            if not canvas:
                return
            
            # Update design layer
            design_layer = await self._generate_design_layer(content)
            canvas["visualization_layers"]["design"]["data"] = design_layer
            
            # Update AI reasoning layer
            reasoning_layer = await self._generate_reasoning_layer(content)
            canvas["visualization_layers"]["ai_reasoning"]["data"] = reasoning_layer
            
            # Update performance layer
            performance_layer = await self._generate_performance_layer(content)
            canvas["visualization_layers"]["performance"]["data"] = performance_layer
            
            # Update trust layer
            trust_layer = await self._generate_trust_layer(content)
            canvas["visualization_layers"]["trust"]["data"] = trust_layer
            
            # Update in Redis
            canvas_key = f"{CANVAS_KEY_PREFIX}{canvas_id}"
            await self.redis.set(canvas_key, json.dumps(canvas), ex=86400)  # 24 hour cache
            
            # Update in database
            await db_update_canvas(canvas)
            
        except Exception as e:
            logger.error(f"Failed to update visualization layers: {e}")
    
    async def _generate_design_layer(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate design visualization layer"""
        try:
            # Extract design elements from content
            design_elements = []
            
            # Process HTML content
            if "html" in content:
                # Extract layout structure
                layout = self._extract_layout_from_html(content["html"])
                
                # Extract color scheme
                colors = self._extract_colors_from_html(content["html"])
                
                # Extract typography
                typography = self._extract_typography_from_html(content["html"])
                
                # Create design layer data
                design_layer = {
                    "layout": layout,
                    "colors": colors,
                    "typography": typography,
                    "elements": design_elements,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                return design_layer
            
            # Process JSON content
            elif "json" in content:
                # Extract layout structure
                layout = self._extract_layout_from_json(content["json"])
                
                # Extract color scheme
                colors = self._extract_colors_from_json(content["json"])
                
                # Extract typography
                typography = self._extract_typography_from_json(content["json"])
                
                # Create design layer data
                design_layer = {
                    "layout": layout,
                    "colors": colors,
                    "typography": typography,
                    "elements": design_elements,
                    "generated_at": datetime.utcnow().isoformat()
                }
                
                return design_layer
            
            # Default empty layer
            return {
                "layout": {},
                "colors": [],
                "typography": {},
                "elements": [],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate design layer: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_reasoning_layer(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI reasoning visualization layer"""
        try:
            # Generate reasoning using LLM
            if "html" in content or "text" in content:
                content_text = content.get("text", content.get("html", ""))
                
                # Generate reasoning using LLM
                prompt = f"""
                Analyze the following email content and provide reasoning about its effectiveness:
                
                {content_text[:2000]}  # Limit to 2000 chars to avoid token limits
                
                Provide analysis in the following JSON format:
                {{
                    "overall_effectiveness": float,  # 0.0 to 1.0
                    "strengths": [string],  # List of strengths
                    "weaknesses": [string],  # List of weaknesses
                    "improvement_suggestions": [string],  # List of suggestions
                    "reasoning": string  # Overall reasoning
                }}
                """
                
                response = await self.llm_client.generate_text(
                    prompt=prompt,
                    model="claude-3-7-sonnet",
                    temperature=0.2,
                    max_tokens=1000
                )
                
                # Parse JSON response
                try:
                    reasoning_data = json.loads(response["content"])
                    
                    # Add timestamp
                    reasoning_data["generated_at"] = datetime.utcnow().isoformat()
                    
                    return reasoning_data
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse reasoning response: {response['content']}")
                    return {
                        "error": "Failed to parse reasoning response",
                        "generated_at": datetime.utcnow().isoformat()
                    }
            
            # Default empty layer
            return {
                "overall_effectiveness": 0.0,
                "strengths": [],
                "weaknesses": [],
                "improvement_suggestions": [],
                "reasoning": "No content provided for analysis",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate reasoning layer: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_performance_layer(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance insights visualization layer"""
        try:
            # Generate performance metrics
            performance_metrics = {
                "estimated_load_time": self._estimate_load_time(content),
                "estimated_engagement": self._estimate_engagement(content),
                "estimated_conversion": self._estimate_conversion(content),
                "estimated_deliverability": self._estimate_deliverability(content),
                "optimization_suggestions": self._generate_optimization_suggestions(content),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Failed to generate performance layer: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_trust_layer(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trust verification visualization layer"""
        try:
            # Generate trust metrics
            trust_metrics = {
                "verification_status": "pending",
                "verification_score": 0.0,
                "verification_details": {
                    "sender_verification": False,
                    "content_verification": False,
                    "link_verification": False,
                    "image_verification": False
                },
                "blockchain_verification": {
                    "enabled": False,
                    "transaction_id": None,
                    "verification_url": None
                },
                "certificate": {
                    "id": None,
                    "url": None,
                    "qr_code": None
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return trust_metrics
            
        except Exception as e:
            logger.error(f"Failed to generate trust layer: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _extract_layout_from_html(self, html: str) -> Dict[str, Any]:
        """Extract layout structure from HTML content"""
        # Simple implementation - in production this would use a proper HTML parser
        layout = {
            "structure": "unknown",
            "sections": []
        }
        
        # Check for common layout patterns
        if "<table" in html:
            layout["structure"] = "table"
            # Count table sections
            table_count = html.count("<table")
            layout["sections"] = [{"type": "table", "index": i} for i in range(table_count)]
        elif "<div" in html:
            layout["structure"] = "div"
            # Count div sections
            div_count = html.count("<div")
            layout["sections"] = [{"type": "div", "index": i} for i in range(div_count)]
        
        return layout
    
    def _extract_colors_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract color scheme from HTML content"""
        # Simple implementation - in production this would use a proper HTML parser and CSS extractor
        colors = []
        
        # Look for hex colors
        import re
        hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', html)
        
        # Look for rgb colors
        rgb_colors = re.findall(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', html)
        
        # Add hex colors
        for color in hex_colors:
            colors.append({
                "type": "hex",
                "value": color,
                "usage": "unknown"
            })
        
        # Add rgb colors
        for r, g, b in rgb_colors:
            colors.append({
                "type": "rgb",
                "value": f"rgb({r}, {g}, {b})",
                "usage": "unknown"
            })
        
        return colors
    
    def _extract_typography_from_html(self, html: str) -> Dict[str, Any]:
        """Extract typography from HTML content"""
        # Simple implementation - in production this would use a proper HTML parser and CSS extractor
        typography = {
            "fonts": [],
            "sizes": [],
            "weights": []
        }
        
        # Look for font families
        import re
        font_families = re.findall(r'font-family:\s*([^;]+)', html)
        
        # Look for font sizes
        font_sizes = re.findall(r'font-size:\s*([^;]+)', html)
        
        # Look for font weights
        font_weights = re.findall(r'font-weight:\s*([^;]+)', html)
        
        # Add font families
        for font in font_families:
            for f in font.split(','):
                f = f.strip().strip("'").strip('"')
                if f and f not in typography["fonts"]:
                    typography["fonts"].append(f)
        
        # Add font sizes
        for size in font_sizes:
            size = size.strip()
            if size and size not in typography["sizes"]:
                typography["sizes"].append(size)
        
        # Add font weights
        for weight in font_weights:
            weight = weight.strip()
            if weight and weight not in typography["weights"]:
                typography["weights"].append(weight)
        
        return typography
    
    def _extract_layout_from_json(self, json_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract layout structure from JSON content"""
        # Simple implementation - in production this would analyze the JSON structure
        layout = {
            "structure": "json",
            "sections": []
        }
        
        # Extract sections from JSON
        if isinstance(json_content, dict):
            for key, value in json_content.items():
                if isinstance(value, dict) and "type" in value:
                    layout["sections"].append({
                        "type": value["type"],
                        "id": key
                    })
        
        return layout
    
    def _extract_colors_from_json(self, json_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract color scheme from JSON content"""
        # Simple implementation - in production this would analyze the JSON structure
        colors = []
        
        # Extract colors from JSON
        def extract_colors_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ["color", "backgroundColor", "borderColor"] and isinstance(value, str):
                        colors.append({
                            "type": "hex" if value.startswith("#") else "name",
                            "value": value,
                            "usage": key,
                            "path": path + "." + key
                        })
                    elif isinstance(value, (dict, list)):
                        extract_colors_recursive(value, path + "." + key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_colors_recursive(item, path + f"[{i}]")
        
        extract_colors_recursive(json_content)
        
        return colors
    
    def _extract_typography_from_json(self, json_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract typography from JSON content"""
        # Simple implementation - in production this would analyze the JSON structure
        typography = {
            "fonts": [],
            "sizes": [],
            "weights": []
        }
        
        # Extract typography from JSON
        def extract_typography_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "fontFamily" and isinstance(value, str):
                        for font in value.split(','):
                            font = font.strip().strip("'").strip('"')
                            if font and font not in typography["fonts"]:
                                typography["fonts"].append(font)
                    elif key == "fontSize" and isinstance(value, str):
                        if value not in typography["sizes"]:
                            typography["sizes"].append(value)
                    elif key == "fontWeight" and isinstance(value, (str, int)):
                        weight = str(value)
                        if weight not in typography["weights"]:
                            typography["weights"].append(weight)
                    elif isinstance(value, (dict, list)):
                        extract_typography_recursive(value, path + "." + key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    extract_typography_recursive(item, path + f"[{i}]")
        
        extract_typography_recursive(json_content)
        
        return typography
    
    def _estimate_load_time(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate load time for email content"""
        # Simple implementation - in production this would use more sophisticated metrics
        load_time = {
            "desktop": 0.0,
            "mobile": 0.0,
            "factors": []
        }
        
        # Estimate based on content size
        content_size = 0
        
        if "html" in content:
            content_size = len(content["html"])
            
            # Check for images
            import re
            image_tags = re.findall(r'<img[^>]+>', content["html"])
            
            # Add image load time
            for img in image_tags:
                load_time["factors"].append({
                    "type": "image",
                    "impact": "medium"
                })
                # Assume average image adds 100ms on desktop, 200ms on mobile
                load_time["desktop"] += 0.1
                load_time["mobile"] += 0.2
        
        # Base load time based on content size
        base_desktop = content_size / 50000  # Assume 50KB loads in 1 second on desktop
        base_mobile = content_size / 20000   # Assume 20KB loads in 1 second on mobile
        
        load_time["desktop"] += base_desktop
        load_time["mobile"] += base_mobile
        
        load_time["factors"].append({
            "type": "content_size",
            "size_bytes": content_size,
            "impact": "low" if content_size < 50000 else "medium" if content_size < 100000 else "high"
        })
        
        return load_time
    
    def _estimate_engagement(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate engagement metrics for email content"""
        # Simple implementation - in production this would use ML models
        engagement = {
            "open_rate": 0.0,
            "click_rate": 0.0,
            "read_time": 0.0,
            "factors": []
        }
        
        # Default values
        engagement["open_rate"] = 0.2  # 20% open rate
        engagement["click_rate"] = 0.05  # 5% click rate
        
        # Adjust based on content
        if "html" in content:
            html = content["html"]
            
            # Estimate read time (5 words per second)
            import re
            words = re.findall(r'\b\w+\b', html)
            word_count = len(words)
            read_time = word_count / 5  # seconds
            
            engagement["read_time"] = read_time
            engagement["factors"].append({
                "type": "content_length",
                "word_count": word_count,
                "impact": "low" if word_count < 100 else "medium" if word_count < 300 else "high"
            })
            
            # Check for links
            links = re.findall(r'<a[^>]+>', html)
            link_count = len(links)
            
            if link_count > 0:
                engagement["click_rate"] += min(0.02 * link_count, 0.1)  # Max 10% boost
                engagement["factors"].append({
                    "type": "links",
                    "count": link_count,
                    "impact": "medium"
                })
            
            # Check for images
            images = re.findall(r'<img[^>]+>', html)
            image_count = len(images)
            
            if image_count > 0:
                engagement["open_rate"] += min(0.05 * image_count, 0.15)  # Max 15% boost
                engagement["factors"].append({
                    "type": "images",
                    "count": image_count,
                    "impact": "high"
                })
        
        return engagement
    
    def _estimate_conversion(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate conversion metrics for email content"""
        # Simple implementation - in production this would use ML models
        conversion = {
            "conversion_rate": 0.0,
            "factors": []
        }
        
        # Default values
        conversion["conversion_rate"] = 0.01  # 1% conversion rate
        
        # Adjust based on content
        if "html" in content:
            html = content["html"]
            
            # Check for call-to-action buttons
            import re
            buttons = re.findall(r'<button[^>]*>.*?</button>|<a[^>]*class="[^"]*button[^"]*"[^>]*>.*?</a>', html, re.IGNORECASE | re.DOTALL)
            button_count = len(buttons)
            
            if button_count > 0:
                conversion["conversion_rate"] += min(0.01 * button_count, 0.05)  # Max 5% boost
                conversion["factors"].append({
                    "type": "cta_buttons",
                    "count": button_count,
                    "impact": "high"
                })
            
            # Check for personalization
            personalization = re.findall(r'\{\{.*?\}\}|\[.*?\]', html)
            personalization_count = len(personalization)
            
            if personalization_count > 0:
                conversion["conversion_rate"] += min(0.005 * personalization_count, 0.03)  # Max 3% boost
                conversion["factors"].append({
                    "type": "personalization",
                    "count": personalization_count,
                    "impact": "medium"
                })
            
            # Check for social proof
            social_proof = re.findall(r'testimonial|review|rating|star|recommend', html, re.IGNORECASE)
            if social_proof:
                conversion["conversion_rate"] += 0.02  # 2% boost
                conversion["factors"].append({
                    "type": "social_proof",
                    "impact": "medium"
                })
        
        return conversion
    
    def _estimate_deliverability(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate deliverability metrics for email content"""
        # Simple implementation - in production this would use more sophisticated metrics
        deliverability = {
            "inbox_placement_rate": 0.0,
            "spam_score": 0.0,
            "factors": []
        }
        
        # Default values
        deliverability["inbox_placement_rate"] = 0.9  # 90% inbox placement
        deliverability["spam_score"] = 2.0  # On a scale of 0-10
        
        # Adjust based on content
        if "html" in content:
            html = content["html"]
            
            # Check for spam trigger words
            import re
            spam_words = [
                "free", "guarantee", "credit", "buy", "order", "purchase",
                "discount", "save", "offer", "limited", "act now", "click here",
                "winner", "congratulations", "selected", "prize", "money"
            ]
            
            spam_word_count = 0
            for word in spam_words:
                spam_word_count += len(re.findall(r'\b' + word + r'\b', html, re.IGNORECASE))
            
            if spam_word_count > 0:
                # Increase spam score based on trigger word count
                deliverability["spam_score"] += min(0.5 * spam_word_count, 5.0)  # Max 5 point increase
                deliverability["factors"].append({
                    "type": "spam_trigger_words",
                    "count": spam_word_count,
                    "impact": "high"
                })
            
            # Check image to text ratio
            text_length = len(re.sub(r'<[^>]*>', '', html))
            image_tags = re.findall(r'<img[^>]+>', html)
            image_count = len(image_tags)
            
            if text_length > 0 and image_count > 0:
                image_text_ratio = image_count / (text_length / 500)  # Normalize text length
                
                if image_text_ratio > 1.0:
                    deliverability["spam_score"] += min(image_text_ratio, 2.0)  # Max 2 point increase
                    deliverability["factors"].append({
                        "type": "high_image_ratio",
                        "ratio": image_text_ratio,
                        "impact": "medium"
                    })
            
            # Check for excessive capitalization
            caps_text = re.findall(r'[A-Z]{4,}', html)
            if caps_text:
                deliverability["spam_score"] += min(0.5 * len(caps_text), 2.0)  # Max 2 point increase
                deliverability["factors"].append({
                    "type": "excessive_caps",
                    "count": len(caps_text),
                    "impact": "medium"
                })
        
        # Calculate inbox placement rate based on spam score
        if deliverability["spam_score"] <= 2.0:
            deliverability["inbox_placement_rate"] = 0.95  # 95% for low spam score
        elif deliverability["spam_score"] <= 5.0:
            deliverability["inbox_placement_rate"] = 0.85  # 85% for medium spam score
        else:
            deliverability["inbox_placement_rate"] = 0.7  # 70% for high spam score
        
        return deliverability
    
    def _generate_optimization_suggestions(self, content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization suggestions for email content"""
        suggestions = []
        
        if "html" in content:
            html = content["html"]
            
            # Check for missing alt text on images
            import re
            images = re.findall(r'<img[^>]+>', html)
            for img in images:
                if 'alt="' not in img or 'alt=""' in img:
                    suggestions.append({
                        "type": "accessibility",
                        "issue": "missing_alt_text",
                        "description": "Add descriptive alt text to images for better accessibility",
                        "priority": "high"
                    })
                    break
            
            # Check for long paragraphs
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.IGNORECASE | re.DOTALL)
            for p in paragraphs:
                # Remove HTML tags for word count
                p_text = re.sub(r'<[^>]*>', '', p)
                words = re.findall(r'\b\w+\b', p_text)
                if len(words) > 50:
                    suggestions.append({
                        "type": "readability",
                        "issue": "long_paragraph",
                        "description": "Break long paragraphs into smaller chunks for better readability",
                        "priority": "medium"
                    })
                    break
            
            # Check for mobile responsiveness
            if "media" not in html and "viewport" not in html:
                suggestions.append({
                    "type": "mobile",
                    "issue": "not_responsive",
                    "description": "Add responsive design elements for better mobile experience",
                    "priority": "high"
                })
            
            # Check for large images
            large_images = re.findall(r'<img[^>]*width=["\'](.*?)["\'][^>]*>', html)
            for width in large_images:
                try:
                    if int(width.replace("px", "")) > 600:
                        suggestions.append({
                            "type": "performance",
                            "issue": "large_images",
                            "description": "Optimize large images to improve load time",
                            "priority": "medium"
                        })
                        break
                except ValueError:
                    pass
        
        return suggestions

# Singleton instance
_cognitive_canvas_instance = None

def get_cognitive_canvas():
    """Get the singleton instance of CognitiveCanvas"""
    global _cognitive_canvas_instance
    if _cognitive_canvas_instance is None:
        _cognitive_canvas_instance = CognitiveCanvas()
    return _cognitive_canvas_instance
