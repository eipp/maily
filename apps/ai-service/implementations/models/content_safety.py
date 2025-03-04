"""
Content Safety Filter for AI Mesh Network

This module implements content safety filtering to ensure all AI-generated content
meets safety and ethical guidelines.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio
import re

from ...utils.llm_client import get_llm_client
from .model_fallback import get_model_fallback_chain

logger = logging.getLogger("ai_service.implementations.models.content_safety")

# Safety categories
SAFETY_CATEGORIES = [
    "hate",
    "harassment",
    "self_harm",
    "sexual",
    "violence",
    "dangerous_content",
    "deception",
    "malware",
    "offensive_language"
]

# Threshold for safety violations (0-1)
DEFAULT_SAFETY_THRESHOLD = 0.8

class ContentSafetyFilter:
    """Content safety filter for AI-generated content"""
    
    def __init__(
        self,
        safety_model: str = "claude-3-7-sonnet",
        safety_threshold: float = DEFAULT_SAFETY_THRESHOLD
    ):
        """
        Initialize the content safety filter
        
        Args:
            safety_model: Model to use for safety filtering
            safety_threshold: Threshold for safety violations (0-1)
        """
        self.safety_model = safety_model
        self.safety_threshold = safety_threshold
        self.llm_client = get_llm_client()
        self.model_fallback = get_model_fallback_chain()
        
        # Performance metrics
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0
        self.processing_time = 0.0
    
    async def check_content_safety(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check content for safety violations
        
        Args:
            content: Content to check
            context: Optional context for safety check
            
        Returns:
            Tuple of (is_safe, safety_result)
        """
        start_time = time.time()
        self.total_checks += 1
        
        try:
            # First check for simple pattern matching
            pattern_result = self._pattern_based_check(content)
            if not pattern_result["is_safe"]:
                self.failed_checks += 1
                self.processing_time += time.time() - start_time
                return False, pattern_result
            
            # If no simple patterns match, use LLM for deeper analysis
            model_result = await self._model_based_check(content, context)
            is_safe = model_result["is_safe"]
            
            # Update metrics
            if is_safe:
                self.passed_checks += 1
            else:
                self.failed_checks += 1
            
            self.processing_time += time.time() - start_time
            return is_safe, model_result
            
        except Exception as e:
            logger.error(f"Error checking content safety: {e}")
            self.failed_checks += 1
            self.processing_time += time.time() - start_time
            
            # Fail open or closed? Here we fail closed for safety
            return False, {
                "is_safe": False,
                "error": str(e),
                "categories": {"error": 1.0},
                "processing_time": time.time() - start_time
            }
    
    def _pattern_based_check(self, content: str) -> Dict[str, Any]:
        """
        Perform pattern-based safety check
        
        Args:
            content: Content to check
            
        Returns:
            Safety result dictionary
        """
        # Convert to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Check for sensitive patterns
        patterns = {
            "malware": [
                r"\b(trojan|virus|malware|exploit|rootkit)\b.*\b(download|install|deploy|inject)\b",
                r"\bhow\s+to\s+(hack|crack|steal|phish)"
            ],
            "dangerous_content": [
                r"\bhow\s+to\s+(make|create|build)\s+(bomb|explosive|weapon)",
                r"\bhow\s+to\s+(poison|kill|harm)\s+(someone|people|person)"
            ],
            "self_harm": [
                r"\bhow\s+to\s+(commit\s+suicide|kill\s+(myself|yourself|oneself))",
                r"\b(best|easiest|painless)\s+ways?\s+to\s+(die|end\s+life)"
            ]
        }
        
        # Check for matches
        violations = {}
        
        for category, category_patterns in patterns.items():
            for pattern in category_patterns:
                if re.search(pattern, content_lower):
                    violations[category] = 1.0
                    break
        
        # Return result
        if violations:
            return {
                "is_safe": False,
                "categories": violations,
                "check_method": "pattern",
                "processing_time": 0.0
            }
        
        # No pattern matches, proceed to model-based check
        return {
            "is_safe": True,
            "categories": {},
            "check_method": "pattern",
            "processing_time": 0.0
        }
    
    async def _model_based_check(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform model-based safety check
        
        Args:
            content: Content to check
            context: Optional context for the check
            
        Returns:
            Safety result dictionary
        """
        start_time = time.time()
        
        # Prepare context information
        context_info = ""
        if context:
            context_info = f"""
# ADDITIONAL CONTEXT
{json.dumps(context, indent=2)}
"""
        
        # Create prompt for safety check
        system_prompt = """You are a content safety evaluator. Your job is to evaluate whether content is safe and appropriate for an email marketing platform. You should flag content that contains:

1. Hate speech or content promoting discrimination
2. Harassment or bullying
3. Content promoting self-harm or suicide
4. Sexually explicit content
5. Graphic violence or gore
6. Dangerous content (instructions for harmful activities)
7. Deceptive content (scams, phishing)
8. Malware, hacking instructions, or illegal activities
9. Highly offensive language

You should be sensitive to context. Content that may be appropriate in some contexts (like medical information) should not be flagged unless presented in an inappropriate way.

Evaluate the content objectively and provide scores for different safety categories.
"""
        
        prompt = f"""# CONTENT TO EVALUATE
{content}

{context_info}

# INSTRUCTIONS
Analyze the content for safety issues and rate it across the following categories:
- hate: Content expressing hatred or prejudice
- harassment: Content intended to harass or bully specific individuals or groups
- self_harm: Content promoting self-harm or suicide
- sexual: Sexually explicit content
- violence: Graphic violence or gore
- dangerous_content: Instructions for harmful activities
- deception: Scams, phishing, or misleading content
- malware: Hacking instructions or promotion of illegal activities
- offensive_language: Highly offensive language

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "is_safe": true or false,
  "reasoning": "Detailed explanation of your safety assessment",
  "categories": {{
    "hate": float between 0 and 1,
    "harassment": float between 0 and 1,
    "self_harm": float between 0 and 1,
    "sexual": float between 0 and 1,
    "violence": float between 0 and 1,
    "dangerous_content": float between 0 and 1,
    "deception": float between 0 and 1,
    "malware": float between 0 and 1,
    "offensive_language": float between 0 and 1
  }},
  "overall_safety_score": float between 0 and 1,
  "recommendation": "ALLOW or BLOCK"
}}
```

Respond only with the JSON object, no additional text.
"""
        
        try:
            # Use model fallback chain for reliability
            result = await self.model_fallback.generate_text(
                prompt=prompt,
                primary_model=self.safety_model,
                system_prompt=system_prompt,
                temperature=0.1  # Low temperature for consistent results
            )
            
            # Parse response
            content_str = result.get("content", "")
            
            try:
                # Try to parse JSON response
                if "```json" in content_str and "```" in content_str.split("```json", 1)[1]:
                    json_content = content_str.split("```json", 1)[1].split("```", 1)[0]
                    safety_result = json.loads(json_content)
                elif "```" in content_str and "```" in content_str.split("```", 1)[1]:
                    json_content = content_str.split("```", 1)[1].split("```", 1)[0]
                    safety_result = json.loads(json_content)
                else:
                    safety_result = json.loads(content_str)
                
                # Add metadata
                safety_result["check_method"] = "model"
                safety_result["model_used"] = result.get("model", self.safety_model)
                safety_result["processing_time"] = time.time() - start_time
                
                # Ensure is_safe is set based on threshold
                max_category_score = max(safety_result.get("categories", {}).values()) if safety_result.get("categories") else 0
                overall_score = safety_result.get("overall_safety_score", max_category_score)
                
                safety_result["is_safe"] = overall_score < self.safety_threshold
                
                return safety_result
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse safety check result: {content_str}")
                return {
                    "is_safe": False,
                    "error": "Failed to parse safety check result",
                    "raw_response": content_str[:1000] + "..." if len(content_str) > 1000 else content_str,
                    "check_method": "model",
                    "processing_time": time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Error in model-based safety check: {e}")
            return {
                "is_safe": False,
                "error": str(e),
                "check_method": "model",
                "processing_time": time.time() - start_time
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the safety filter
        
        Returns:
            Dictionary with performance metrics
        """
        avg_processing_time = 0
        if self.total_checks > 0:
            avg_processing_time = self.processing_time / self.total_checks
        
        return {
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "pass_rate": self.passed_checks / max(1, self.total_checks),
            "total_processing_time": self.processing_time,
            "avg_processing_time": avg_processing_time,
            "safety_threshold": self.safety_threshold,
            "safety_model": self.safety_model
        }
    
    async def sanitize_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Sanitize content to remove unsafe elements
        
        Args:
            content: Content to sanitize
            context: Optional context for sanitization
            
        Returns:
            Tuple of (sanitized_content, sanitization_result)
        """
        # First check if content is already safe
        is_safe, safety_result = await self.check_content_safety(content, context)
        
        if is_safe:
            return content, {
                "is_sanitized": False,
                "original_safe": True,
                "changes_made": [],
                "safety_result": safety_result
            }
        
        # Content is not safe, sanitize it
        start_time = time.time()
        
        # Prepare context information
        context_info = ""
        if context:
            context_info = f"""
# ADDITIONAL CONTEXT
{json.dumps(context, indent=2)}
"""
        
        # Create prompt for sanitization
        system_prompt = """You are a content safety filter. Your job is to sanitize potentially unsafe content while preserving the original intent as much as possible. Focus on removing or replacing:

1. Hate speech or content promoting discrimination
2. Harassment or bullying
3. Content promoting self-harm or suicide
4. Sexually explicit content
5. Graphic violence or gore
6. Dangerous content (instructions for harmful activities)
7. Deceptive content (scams, phishing)
8. Malware, hacking instructions, or illegal activities
9. Highly offensive language

Make the minimum necessary changes to make the content safe while preserving the original intent and meaning as much as possible. If the entire content is fundamentally unsafe or cannot be sanitized, provide a brief explanation of why it cannot be made safe.
"""
        
        prompt = f"""# UNSAFE CONTENT TO SANITIZE
{content}

{context_info}

# SAFETY ISSUES DETECTED
{json.dumps(safety_result.get("categories", {}), indent=2)}

Reasoning: {safety_result.get("reasoning", "Safety issues detected in the content.")}

# INSTRUCTIONS
Sanitize the content by removing or replacing unsafe elements while preserving the original intent and meaning as much as possible. Make only the changes necessary to address the safety issues identified.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "sanitized_content": "The sanitized version of the content",
  "changes_made": [
    "Description of change 1",
    "Description of change 2"
  ],
  "can_be_sanitized": true or false,
  "explanation": "Explanation of why the content could or could not be fully sanitized"
}}
```

Respond only with the JSON object, no additional text.
"""
        
        try:
            # Use model fallback chain for reliability
            result = await self.model_fallback.generate_text(
                prompt=prompt,
                primary_model=self.safety_model,
                system_prompt=system_prompt,
                temperature=0.2  # Low temperature for consistent results
            )
            
            # Parse response
            content_str = result.get("content", "")
            
            try:
                # Try to parse JSON response
                if "```json" in content_str and "```" in content_str.split("```json", 1)[1]:
                    json_content = content_str.split("```json", 1)[1].split("```", 1)[0]
                    sanitization_result = json.loads(json_content)
                elif "```" in content_str and "```" in content_str.split("```", 1)[1]:
                    json_content = content_str.split("```", 1)[1].split("```", 1)[0]
                    sanitization_result = json.loads(json_content)
                else:
                    sanitization_result = json.loads(content_str)
                
                # Get sanitized content
                sanitized_content = sanitization_result.get("sanitized_content", content)
                can_be_sanitized = sanitization_result.get("can_be_sanitized", True)
                
                # Check if sanitized content is safe
                is_sanitized_safe, sanitized_safety_result = await self.check_content_safety(sanitized_content, context)
                
                # Add metadata
                sanitization_result["is_sanitized"] = True
                sanitization_result["original_safe"] = False
                sanitization_result["sanitized_safe"] = is_sanitized_safe
                sanitization_result["model_used"] = result.get("model", self.safety_model)
                sanitization_result["processing_time"] = time.time() - start_time
                sanitization_result["safety_result"] = safety_result
                sanitization_result["sanitized_safety_result"] = sanitized_safety_result
                
                # Return sanitized content and result
                if can_be_sanitized and is_sanitized_safe:
                    return sanitized_content, sanitization_result
                else:
                    # Content cannot be safely sanitized
                    return "", {
                        "is_sanitized": True,
                        "original_safe": False,
                        "sanitized_safe": False,
                        "can_be_sanitized": False,
                        "explanation": sanitization_result.get("explanation", "Content cannot be safely sanitized"),
                        "processing_time": time.time() - start_time,
                        "safety_result": safety_result
                    }
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse sanitization result: {content_str}")
                return "", {
                    "is_sanitized": False,
                    "error": "Failed to parse sanitization result",
                    "raw_response": content_str[:1000] + "..." if len(content_str) > 1000 else content_str,
                    "processing_time": time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Error in content sanitization: {e}")
            return "", {
                "is_sanitized": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

# Singleton instance
_content_safety_filter_instance = None

def get_content_safety_filter() -> ContentSafetyFilter:
    """Get the singleton instance of ContentSafetyFilter"""
    global _content_safety_filter_instance
    if _content_safety_filter_instance is None:
        _content_safety_filter_instance = ContentSafetyFilter()
    return _content_safety_filter_instance