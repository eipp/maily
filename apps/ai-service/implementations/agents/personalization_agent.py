"""
Personalization Agent for AI Mesh Network

This module implements the Personalization Agent, which specializes in adapting email content
and design to individual recipients based on their preferences, behavior, and demographics.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry
from .base_agent import BaseAgent

logger = logging.getLogger("ai_service.implementations.agents.personalization_agent")

@BaseAgent.register_agent_type("personalization")
class PersonalizationAgent(BaseAgent):
    """Agent specialized in content and design personalization"""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the Personalization Agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        # Set default values for personalization agent
        if "name" not in agent_config:
            agent_config["name"] = "Personalization Specialist"
        
        if "type" not in agent_config:
            agent_config["type"] = "personalization"
            
        if "description" not in agent_config:
            agent_config["description"] = "Specializes in adapting email content and design to individual recipients"
            
        if "capabilities" not in agent_config:
            agent_config["capabilities"] = [
                "content_personalization", 
                "segment_specific_messaging", 
                "dynamic_recommendations",
                "behavioral_adaptation",
                "template_customization"
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
        Process a personalization-related task
        
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
            logger.error(f"Personalization agent {self.agent_id} failed to process task: {e}")
            
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
                "personalization_recommendations": None,
                "confidence": 0.0,
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
        Determine the type of personalization task
        
        Args:
            task: Task description
            
        Returns:
            Task type (content, segment, recommendations, behavioral, template)
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["content", "message", "text", "copy", "narrative"]):
            return "content"
        elif any(keyword in task_lower for keyword in ["segment", "group", "audience", "category", "demographic"]):
            return "segment"
        elif any(keyword in task_lower for keyword in ["recommend", "suggestion", "products", "services"]):
            return "recommendations"
        elif any(keyword in task_lower for keyword in ["behavior", "activity", "history", "engagement"]):
            return "behavioral"
        elif any(keyword in task_lower for keyword in ["template", "format", "structure", "layout"]):
            return "template"
        else:
            # Default to content personalization
            return "content"
    
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
            task_type: Type of task (content, segment, recommendations, behavioral, template)
            context: Context for the task
            
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Extract context elements
        recipient_data = context.get("recipient_data", {})
        user_segments = context.get("user_segments", [])
        user_history = context.get("user_history", {})
        user_preferences = context.get("user_preferences", {})
        base_template = context.get("base_template", "")
        original_content = context.get("original_content", "")
        campaign_goal = context.get("campaign_goal", "")
        personalization_level = context.get("personalization_level", "medium")
        
        # Format shared context
        shared_context = f"""
# RECIPIENT DATA
{json.dumps(recipient_data, indent=2) if isinstance(recipient_data, dict) else recipient_data}

# USER SEGMENTS
{json.dumps(user_segments, indent=2) if isinstance(user_segments, list) else user_segments}

# USER PREFERENCES
{json.dumps(user_preferences, indent=2) if isinstance(user_preferences, dict) else user_preferences}

# CAMPAIGN GOAL
{campaign_goal}

# PERSONALIZATION LEVEL
{personalization_level}
"""

        # Generate system prompt based on task type
        if task_type == "content":
            system_prompt = f"""You are a personalization specialist focusing on email content adaptation. Your role is to tailor messaging to individual recipients based on their profile, preferences, and behavior to increase relevance and engagement.

Your content personalization approach includes:
1. Adapting tone, style, and language to match recipient preferences
2. Incorporating personal details in a natural, non-intrusive way
3. Creating variations of key messages optimized for different user types
4. Ensuring consistent brand voice while personalizing content
5. Adjusting content depth and detail based on recipient engagement patterns

When personalizing content, consider:
- The appropriate level of formality based on recipient relationship
- Cultural context and language preferences
- Previous interactions and engagement history
- Personal milestones or relevant timely content
- Privacy and ethical considerations in personalization
"""
            
            prompt = f"""# CONTENT PERSONALIZATION TASK
{task}

{shared_context}

# USER HISTORY
{json.dumps(user_history, indent=2) if isinstance(user_history, dict) else user_history}

# ORIGINAL CONTENT
{original_content}

# INSTRUCTIONS
Please personalize the content based on the task description and recipient information provided.
Adapt the messaging to increase relevance and engagement while maintaining brand consistency.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to personalizing this content",
  "personalized_content": "The fully personalized content, ready to use",
  "personalization_elements": [
    {{
      "original_element": "Original piece of content",
      "personalized_element": "Personalized version",
      "personalization_factor": "Specific factor that drove this personalization",
      "expected_impact": "Anticipated effect on recipient engagement"
    }},
    // Additional personalization elements...
  ],
  "a_b_test_variations": [
    {{
      "variation": "Alternative personalized version to test",
      "hypothesis": "What this variation aims to test"
    }},
    // Additional test variations...
  ],
  "confidence": float between 0 and 1,
  "considerations": [
    "Important consideration 1 for implementation",
    "Important consideration 2 for implementation"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "segment":
            system_prompt = f"""You are a personalization specialist focusing on segment-specific messaging for email campaigns. Your role is to create tailored content variations for different audience segments based on their characteristics, interests, and behaviors.

Your segment-specific messaging approach includes:
1. Identifying key differences and needs across segments
2. Adapting core messaging to address segment-specific priorities
3. Adjusting value propositions to align with segment motivations
4. Optimizing calls-to-action for different segment behaviors
5. Creating specialized content blocks for different segments

When creating segment-specific messaging, consider:
- The defining characteristics of each segment
- Different motivations and objections across segments
- How segments differ in their customer journey
- Segment-specific language and terminology preferences
- Balance between segment customization and operational efficiency
"""
            
            prompt = f"""# SEGMENT-SPECIFIC MESSAGING TASK
{task}

{shared_context}

# USER SEGMENTS
{json.dumps(user_segments, indent=2) if isinstance(user_segments, list) else user_segments}

# ORIGINAL CONTENT
{original_content}

# INSTRUCTIONS
Please create segment-specific messaging variations based on the task description and segment information provided.
Adapt the content to address the unique needs, interests, and behaviors of each segment.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to creating segment-specific messaging",
  "segment_variations": [
    {{
      "segment": "Segment name or identifier",
      "segment_characteristics": [
        "Key characteristic 1",
        "Key characteristic 2"
      ],
      "personalized_content": "The full content variation for this segment",
      "key_adjustments": [
        "Major adjustment 1 made for this segment",
        "Major adjustment 2 made for this segment"
      ],
      "personalized_cta": "Segment-specific call to action"
    }},
    // Additional segment variations...
  ],
  "shared_content_elements": [
    "Content element 1 that remains consistent across segments",
    "Content element 2 that remains consistent across segments"
  ],
  "implementation_approach": "Recommendation for how to implement these variations technically",
  "confidence": float between 0 and 1,
  "testing_recommendations": [
    "Testing recommendation 1",
    "Testing recommendation 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "recommendations":
            system_prompt = f"""You are a personalization specialist focusing on dynamic recommendations for email campaigns. Your role is to create relevant product, content, or action suggestions for recipients based on their interests, behavior, and profile.

Your dynamic recommendations approach includes:
1. Analyzing user behavior and preferences to identify relevant suggestions
2. Prioritizing recommendations based on likelihood of engagement
3. Creating contextually appropriate recommendation presentations
4. Balancing personalized and exploratory recommendations
5. Considering timing and sequence in recommendation strategy

When creating recommendations, consider:
- Recent user interactions and interests
- Similar users' behaviors and preferences
- Complementary items or content to past engagements
- Business priorities balanced with user relevance
- The right level of recommendation specificity for the campaign context
"""
            
            prompt = f"""# DYNAMIC RECOMMENDATIONS TASK
{task}

{shared_context}

# USER HISTORY
{json.dumps(user_history, indent=2) if isinstance(user_history, dict) else user_history}

# INSTRUCTIONS
Please create personalized recommendations based on the task description and user data provided.
Generate relevant product, content, or action suggestions that will maximize engagement and value.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your methodology for generating these recommendations",
  "primary_recommendations": [
    {{
      "item": "Recommended item or content",
      "recommendation_type": "Product/Content/Action/Other",
      "rationale": "Why this is recommended for this user",
      "presentation": "Suggested way to present this recommendation",
      "relevance_score": float between 0 and 1
    }},
    // Additional primary recommendations...
  ],
  "secondary_recommendations": [
    {{
      "item": "Secondary recommended item or content",
      "recommendation_type": "Product/Content/Action/Other",
      "rationale": "Why this is included as a secondary recommendation",
      "relevance_score": float between 0 and 1
    }},
    // Additional secondary recommendations...
  ],
  "exploratory_recommendation": {{
    "item": "Item to broaden user horizons",
    "rationale": "Why this might interest the user despite no direct signals"
  }},
  "fallback_recommendations": [
    "Fallback recommendation 1",
    "Fallback recommendation 2"
  ],
  "confidence": float between 0 and 1,
  "implementation_notes": [
    "Implementation note 1",
    "Implementation note 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "behavioral":
            system_prompt = f"""You are a personalization specialist focusing on behavioral adaptation in email campaigns. Your role is to adjust content based on recipient past behaviors, engagement patterns, and activity history to increase relevance and effectiveness.

Your behavioral adaptation approach includes:
1. Analyzing engagement patterns to determine optimal content approach
2. Adapting messaging based on past user actions and interactions
3. Adjusting content depth and complexity for different engagement levels
4. Recognizing and responding to behavioral signals and triggers
5. Creating behavioral journey-aware content variations

When adapting based on behavior, consider:
- Recent engagement trends and changes in behavior
- Position in the customer lifecycle
- Response to previous similar communications
- Frequency of interaction with different content types
- Behavioral indicators of interest or intent
"""
            
            prompt = f"""# BEHAVIORAL ADAPTATION TASK
{task}

{shared_context}

# USER HISTORY
{json.dumps(user_history, indent=2) if isinstance(user_history, dict) else user_history}

# ORIGINAL CONTENT
{original_content}

# INSTRUCTIONS
Please adapt the content based on the recipient's behavioral patterns and engagement history.
Create variations that respond to past behaviors to increase relevance and effectiveness.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of behavioral patterns and adaptation approach",
  "behavioral_insights": [
    "Key insight 1 about the user's behavior",
    "Key insight 2 about the user's behavior"
  ],
  "engagement_level": "Assessment of overall engagement level",
  "adapted_content": "The fully adapted content based on behavioral insights",
  "key_adaptations": [
    {{
      "behavioral_trigger": "Specific behavior or pattern identified",
      "adaptation": "Content adjustment made in response",
      "rationale": "Why this adaptation is appropriate for this behavior"
    }},
    // Additional adaptations...
  ],
  "engagement_strategy": "Overall strategy for engaging this user based on behavior",
  "recommended_follow_up": "Suggested next communication based on expected response",
  "confidence": float between 0 and 1,
  "behavioral_metrics_to_track": [
    "Metric 1 to monitor after this communication",
    "Metric 2 to monitor after this communication"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "template":
            system_prompt = f"""You are a personalization specialist focusing on email template customization. Your role is to adapt email templates and layouts based on recipient preferences, behavior patterns, and characteristics to optimize engagement and effectiveness.

Your template customization approach includes:
1. Adapting layout structure to match recipient engagement patterns
2. Customizing visual elements based on recipient preferences
3. Adjusting content density and complexity for different users
4. Optimizing for recipient's typical device usage and viewing context
5. Creating cohesive personalized experiences across template elements

When customizing templates, consider:
- How the recipient typically engages with emails
- Visual preferences indicated by past behavior
- Accessibility needs and usability considerations
- Technical limitations of email clients
- Maintaining brand consistency while personalizing
"""
            
            prompt = f"""# TEMPLATE CUSTOMIZATION TASK
{task}

{shared_context}

# USER HISTORY
{json.dumps(user_history, indent=2) if isinstance(user_history, dict) else user_history}

# BASE TEMPLATE
{base_template}

# INSTRUCTIONS
Please customize the email template based on the recipient's preferences and behavior patterns.
Adapt the layout and structure to optimize engagement while maintaining brand consistency.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to customizing this template",
  "template_customizations": [
    {{
      "element": "Template element to customize",
      "customization": "Specific change to make",
      "rationale": "Why this customization suits this recipient",
      "implementation_details": "Technical details for implementation"
    }},
    // Additional customizations...
  ],
  "layout_structure": "Description of the optimized layout structure",
  "visual_elements": {{
    "color_scheme": "Recommended color scheme based on preferences",
    "imagery": "Guidance on imagery selection",
    "typography": "Typography recommendations"
  }},
  "content_presentation": {{
    "density": "Recommended content density (high/medium/low)",
    "hierarchy": "Suggested content hierarchy",
    "emphasis": "Elements to emphasize"
  }},
  "device_optimizations": [
    {{
      "device_type": "Device type to optimize for",
      "specific_adjustments": [
        "Adjustment 1 for this device",
        "Adjustment 2 for this device"
      ]
    }},
    // Additional device optimizations...
  ],
  "confidence": float between 0 and 1,
  "technical_considerations": [
    "Technical consideration 1",
    "Technical consideration 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        else:
            # Default generic prompt
            system_prompt = f"""You are a personalization specialist for email marketing campaigns. Your role is to tailor content, design, and messaging to individual recipients to maximize relevance and engagement.

Apply your expertise to complete the requested task with high quality, considering:
- The recipient's profile, preferences, and behavioral history
- The campaign's goals and core message
- Balance between personalization and privacy
- Technical implementation considerations
- Measurable impact of personalization approaches
"""
            
            prompt = f"""# PERSONALIZATION TASK
{task}

{shared_context}

# USER HISTORY
{json.dumps(user_history, indent=2) if isinstance(user_history, dict) else user_history}

# ORIGINAL CONTENT
{original_content}

# INSTRUCTIONS
Please complete the personalization task based on the description and recipient data provided.
Deliver high-quality personalization that balances relevance, engagement, and implementation feasibility.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to this personalization task",
  "personalization_solution": "The core output of your personalization work",
  "key_personalization_elements": [
    {{
      "element": "Element being personalized",
      "approach": "How it's personalized",
      "expected_impact": "Anticipated effect on engagement"
    }},
    // Additional elements...
  ],
  "implementation_guidance": "Technical guidance for implementing this personalization",
  "confidence": float between 0 and 1,
  "testing_recommendations": [
    "Testing recommendation 1",
    "Testing recommendation 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        return prompt, system_prompt


# Agent factory function
def create_personalization_agent(agent_id: str, agent_config: Dict[str, Any]) -> PersonalizationAgent:
    """
    Create a new personalization agent
    
    Args:
        agent_id: Unique identifier for this agent
        agent_config: Configuration for this agent
        
    Returns:
        PersonalizationAgent instance
    """
    return PersonalizationAgent(agent_id, agent_config)