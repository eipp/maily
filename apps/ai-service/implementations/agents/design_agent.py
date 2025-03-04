"""
Design Agent for AI Mesh Network

This module implements the Design Agent, which specializes in providing design recommendations,
layout analysis, and visual planning for email campaigns.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry
from .base_agent import BaseAgent

logger = logging.getLogger("ai_service.implementations.agents.design_agent")

@BaseAgent.register_agent_type("design")
class DesignAgent(BaseAgent):
    """Agent specialized in design recommendations and visual planning"""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the Design Agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        # Set default values for design agent
        if "name" not in agent_config:
            agent_config["name"] = "Design Specialist"
        
        if "type" not in agent_config:
            agent_config["type"] = "design"
            
        if "description" not in agent_config:
            agent_config["description"] = "Specializes in email design, layout, and visual elements"
            
        if "capabilities" not in agent_config:
            agent_config["capabilities"] = [
                "design_recommendations", 
                "layout_analysis", 
                "visual_planning",
                "accessibility_advice",
                "responsive_design"
            ]
        
        # Initialize base agent
        super().__init__(agent_id, agent_config)
    
    async def process_task(
        self,
        task: str,
        context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a design-related task
        
        Args:
            task: Task description
            context: Context for the task
            system_prompt: Optional system prompt
            
        Returns:
            Dictionary with results
        """
        self.total_requests += 1
        start_time = time.time()
        self.update_status("working")
        
        try:
            # Determine the task type
            task_type = self._determine_task_type(task)
            
            # Generate appropriate prompt based on task type
            prompt, specialized_system_prompt = self._generate_prompt(task, task_type, context)
            
            # Use task-specific system prompt if provided, otherwise use the specialized one
            final_system_prompt = system_prompt or specialized_system_prompt
            
            # Execute LLM request with circuit breaker and retry logic
            result = await self._execute_llm_with_protection(prompt, final_system_prompt)
            
            # Process the result
            processed_result = self.process_llm_result(result)
            
            # Update metrics
            execution_time = time.time() - start_time
            self.total_processing_time += execution_time
            self.successful_requests += 1
            
            # Add metadata to result
            processed_result["metadata"] = {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "task_type": task_type,
                "model_used": result.get("model", self.model),
                "execution_time": execution_time,
                "timestamp": time.time()
            }
            
            # Update status and task history
            self.update_status("idle")
            self.last_processed_task = {
                "task": task,
                "task_type": task_type,
                "timestamp": time.time(),
                "success": True
            }
            self.task_history.append(self.last_processed_task)
            
            return processed_result
            
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Design agent {self.agent_id} failed to process task: {e}")
            
            # Update status and task history
            self.update_status("error")
            failed_task = {
                "task": task,
                "task_type": self._determine_task_type(task),
                "timestamp": time.time(),
                "success": False,
                "error": str(e)
            }
            self.last_processed_task = failed_task
            self.task_history.append(failed_task)
            
            # Return error result
            return {
                "error": str(e),
                "design_recommendations": None,
                "confidence": 0.0,
                "suggestions": [],
                "status": "error",
                "metadata": {
                    "agent_id": self.agent_id,
                    "agent_name": self.name,
                    "execution_time": time.time() - start_time,
                    "timestamp": time.time()
                }
            }
    
    def _determine_task_type(self, task: str) -> str:
        """
        Determine the type of design task
        
        Args:
            task: Task description
            
        Returns:
            Task type (recommendations, layout, visual_planning, accessibility)
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["recommend", "suggest", "advice", "ideas"]):
            return "recommendations"
        elif any(keyword in task_lower for keyword in ["layout", "structure", "format", "organize"]):
            return "layout"
        elif any(keyword in task_lower for keyword in ["visual", "design", "color", "palette", "style"]):
            return "visual_planning"
        elif any(keyword in task_lower for keyword in ["accessibility", "accessible", "ada", "wcag"]):
            return "accessibility"
        elif any(keyword in task_lower for keyword in ["responsive", "mobile", "device"]):
            return "responsive"
        else:
            # Default to recommendations
            return "recommendations"
    
    def _generate_prompt(
        self, 
        task: str, 
        task_type: str, 
        context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Generate prompt for the given task type
        
        Args:
            task: Task description
            task_type: Type of task (recommendations, layout, visual_planning, accessibility, responsive)
            context: Context for the task
            
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Extract context elements
        brand_colors = context.get("brand_colors", {})
        brand_style = context.get("brand_style", "")
        audience = context.get("audience", "general")
        email_platform = context.get("email_platform", "generic")
        existing_design = context.get("existing_design", "")
        email_content = context.get("email_content", "")
        campaign_goal = context.get("campaign_goal", "inform subscribers")
        
        # Format shared context
        shared_context = f"""
# BRAND ELEMENTS
Brand Colors: {json.dumps(brand_colors, indent=2) if isinstance(brand_colors, dict) else brand_colors}
Brand Style: {brand_style}

# AUDIENCE
{audience}

# CAMPAIGN GOAL
{campaign_goal}

# EMAIL PLATFORM
{email_platform}
"""

        # Generate system prompt based on task type
        if task_type == "recommendations":
            system_prompt = f"""You are a design specialist for email marketing campaigns. Your expertise lies in creating visually appealing and effective email designs that enhance user engagement and support marketing goals.

Your design recommendations follow these principles:
1. Maintain brand consistency while creating visual interest
2. Focus on readability and scanability across devices
3. Use visual hierarchy to guide attention to key elements
4. Employ white space strategically to prevent visual overload
5. Consider accessibility and ensure sufficient contrast

When providing design recommendations, consider:
- The email platform's technical limitations
- Mobile-first design principles
- Visual storytelling that supports the message
- Design elements that reinforce call-to-action visibility
- Color psychology appropriate to the audience and message
"""
            
            prompt = f"""# DESIGN RECOMMENDATIONS TASK
{task}

{shared_context}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please provide comprehensive design recommendations based on the task description and context provided.
Ensure the recommendations align with the brand style, consider the audience, and support the campaign goal.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your thought process behind the design recommendations",
  "design_recommendations": {{
    "color_palette": ["Primary color", "Secondary color", "Accent color"],
    "typography": "Recommendations for fonts and text styling",
    "layout_structure": "Overall layout recommendation",
    "visual_elements": "Suggestions for images, icons, or other visual elements",
    "hierarchy": "Recommendations for visual hierarchy"
  }},
  "mockup_description": "Detailed description of how the email would look with these recommendations",
  "confidence": float between 0 and 1,
  "considerations": [
    "Important consideration 1 for implementation",
    "Important consideration 2 for implementation"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "layout":
            system_prompt = f"""You are a layout specialist for email marketing campaigns. Your expertise lies in structuring email content for maximum impact, readability, and conversion.

Your layout analysis approach includes:
1. Organizing content in a logical, scannable flow
2. Creating clear visual hierarchy for different content sections
3. Optimizing placement of headlines, body text, images, and CTAs
4. Ensuring responsive design principles are followed
5. Balancing content density with white space

When analyzing layouts, consider:
- The natural eye movement patterns of readers (F-pattern, Z-pattern)
- Importance of above-the-fold content placement
- Grouping related elements for cognitive ease
- Consistent spacing and alignment
- Headers, footers, and navigation elements
"""
            
            prompt = f"""# LAYOUT ANALYSIS TASK
{task}

{shared_context}

# EXISTING DESIGN
{existing_design}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please analyze the layout needs based on the task description, existing design, and content provided.
Provide detailed recommendations for structuring the email layout to maximize effectiveness.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of layout needs and considerations",
  "layout_structure": [
    {{
      "section": "Section name (e.g., 'Header')",
      "content_elements": ["Element 1", "Element 2"],
      "positioning": "Placement recommendation",
      "importance": "Priority level (High/Medium/Low)"
    }},
    // Additional sections...
  ],
  "spacing_recommendations": "Recommendations for margins, padding, and white space",
  "alignment_strategy": "Recommendations for text and element alignment",
  "responsive_considerations": "How the layout should adapt for mobile devices",
  "confidence": float between 0 and 1,
  "notes": [
    "Important note 1 about the layout",
    "Important note 2 about the layout"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "visual_planning":
            system_prompt = f"""You are a visual design specialist for email marketing campaigns. Your expertise lies in creating cohesive visual styles that strengthen brand identity and enhance message effectiveness.

Your visual planning approach includes:
1. Developing harmonious color schemes that align with brand guidelines
2. Selecting typography that balances readability with brand personality
3. Recommending appropriate imagery, icons, and graphical elements
4. Creating visual continuity throughout the email
5. Ensuring visual elements support the message and call-to-action

When planning visuals, consider:
- Color theory and psychology in relation to the audience and message
- Visual weight and balance across the email
- Contrast between elements to guide attention
- Consistent visual language that reinforces brand identity
- Technical limitations of email clients for image display
"""
            
            prompt = f"""# VISUAL PLANNING TASK
{task}

{shared_context}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please develop a comprehensive visual plan based on the task description and context provided.
Detail how visual elements should be designed and implemented to create a cohesive, effective email.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your rationale for the visual design decisions",
  "color_strategy": {{
    "primary_palette": ["Color 1 with hex code", "Color 2 with hex code"],
    "accent_colors": ["Accent 1 with hex code", "Accent 2 with hex code"],
    "usage_guidelines": "How different colors should be applied"
  }},
  "typography": {{
    "headings": "Font recommendation with size and weight",
    "body_text": "Font recommendation with size and weight",
    "cta_text": "Font recommendation with size and weight"
  }},
  "imagery": {{
    "style": "Description of recommended image style",
    "subjects": "Recommended image subjects",
    "treatment": "Any special treatments or effects"
  }},
  "graphical_elements": [
    "Description of recommended graphical element 1",
    "Description of recommended graphical element 2"
  ],
  "confidence": float between 0 and 1,
  "technical_considerations": [
    "Technical consideration 1 for implementation",
    "Technical consideration 2 for implementation"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "accessibility":
            system_prompt = f"""You are an accessibility specialist for email marketing campaigns. Your expertise lies in ensuring email designs are accessible to all users, including those with disabilities.

Your accessibility approach includes:
1. Ensuring sufficient color contrast for readability
2. Recommending proper heading structure and reading order
3. Providing alt text guidelines for images
4. Ensuring functionality without reliance on color alone
5. Making emails navigable for screen readers

When addressing accessibility, consider:
- WCAG 2.1 AA compliance standards
- The diverse needs of users with visual, motor, auditory, or cognitive disabilities
- Keyboard accessibility for interactive elements
- Text alternatives for non-text content
- Simple, consistent navigation and structure
"""
            
            prompt = f"""# ACCESSIBILITY TASK
{task}

{shared_context}

# EXISTING DESIGN
{existing_design}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please analyze the accessibility requirements based on the task description and context provided.
Provide detailed recommendations to ensure the email is accessible to all users, including those with disabilities.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of accessibility requirements",
  "wcag_considerations": [
    {{
      "principle": "WCAG principle (e.g., 'Perceivable')",
      "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
      ]
    }},
    // Additional principles...
  ],
  "color_contrast": "Recommendations for ensuring sufficient color contrast",
  "screen_reader_optimization": "Guidelines for making content screen reader friendly",
  "alt_text_guidelines": "Recommendations for effective alt text",
  "keyboard_accessibility": "Recommendations for keyboard navigation",
  "confidence": float between 0 and 1,
  "testing_recommendations": [
    "Recommended test 1 to verify accessibility",
    "Recommended test 2 to verify accessibility"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "responsive":
            system_prompt = f"""You are a responsive design specialist for email marketing campaigns. Your expertise lies in ensuring emails display optimally across all devices and screen sizes.

Your responsive design approach includes:
1. Applying mobile-first design principles
2. Creating fluid layouts that adapt to screen dimensions
3. Optimizing images and media for different devices
4. Ensuring touch targets are appropriately sized for mobile
5. Maintaining readability without requiring zoom on small screens

When planning responsive emails, consider:
- Varying screen sizes from small mobile to large desktop displays
- Email client rendering differences
- Loading times on mobile networks
- Text readability at different sizes
- Stackable content blocks for mobile views
"""
            
            prompt = f"""# RESPONSIVE DESIGN TASK
{task}

{shared_context}

# EXISTING DESIGN
{existing_design}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please provide detailed responsive design recommendations based on the task description and context provided.
Ensure the email will display optimally across all devices and screen sizes.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of responsive design requirements",
  "breakpoints": [
    {{
      "device_category": "Device category (e.g., 'Mobile')",
      "max_width": "Maximum width in pixels",
      "layout_changes": [
        "Layout change 1 for this breakpoint",
        "Layout change 2 for this breakpoint"
      ]
    }},
    // Additional breakpoints...
  ],
  "image_strategy": "Recommendations for responsive images",
  "font_size_strategy": "Recommendations for responsive typography",
  "touch_target_guidelines": "Guidelines for touch-friendly elements",
  "email_client_considerations": [
    {{
      "client": "Email client name",
      "special_handling": "Specific adjustments needed"
    }},
    // Additional clients...
  ],
  "confidence": float between 0 and 1,
  "testing_recommendations": [
    "Recommended device/client 1 to test",
    "Recommended device/client 2 to test"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        else:
            # Default generic prompt
            system_prompt = f"""You are a design specialist for email marketing campaigns. Your role is to provide expert guidance on visual design, layout, and user experience to maximize campaign effectiveness.

Apply your expertise to complete the requested task with high quality, considering:
- The brand's visual identity and style guidelines
- The target audience's preferences and behaviors
- The specific goals of the campaign
- Best practices in email design and accessibility
- Technical limitations of email clients
"""
            
            prompt = f"""# DESIGN TASK
{task}

{shared_context}

# EXISTING DESIGN (if applicable)
{existing_design if existing_design else "None provided."}

# EMAIL CONTENT
{email_content}

# INSTRUCTIONS
Please complete the design task based on the description and context provided.
Deliver high-quality design recommendations that meet the specific requirements of the task.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your thought process for completing this task",
  "design_solution": "The primary output of your task",
  "confidence": float between 0 and 1,
  "additional_recommendations": [
    "Additional recommendation 1",
    "Additional recommendation 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        return prompt, system_prompt


# Agent factory function
def create_design_agent(agent_id: str, agent_config: Dict[str, Any]) -> DesignAgent:
    """
    Create a new design agent
    
    Args:
        agent_id: Unique identifier for this agent
        agent_config: Configuration for this agent
        
    Returns:
        DesignAgent instance
    """
    return DesignAgent(agent_id, agent_config)