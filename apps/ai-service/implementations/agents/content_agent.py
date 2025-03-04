"""
Content Agent for AI Mesh Network

This module implements the Content Agent, which specializes in generating,
analyzing, and optimizing content for email campaigns.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry
from .base_agent import BaseAgent

logger = logging.getLogger("ai_service.implementations.agents.content_agent")

@BaseAgent.register_agent_type("content")
class ContentAgent(BaseAgent):
    """Agent specialized in content generation and optimization"""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the Content Agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        # Set default values for content agent
        if "name" not in agent_config:
            agent_config["name"] = "Content Specialist"
        
        if "type" not in agent_config:
            agent_config["type"] = "content"
            
        if "description" not in agent_config:
            agent_config["description"] = "Specializes in generating and refining content"
            
        if "capabilities" not in agent_config:
            agent_config["capabilities"] = [
                "content_generation", 
                "content_editing", 
                "content_analysis"
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
        Process a content-related task
        
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
            logger.error(f"Content agent {self.agent_id} failed to process task: {e}")
            
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
                "content": None,
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
        Determine the type of content task
        
        Args:
            task: Task description
            
        Returns:
            Task type (generation, editing, analysis, evaluation)
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["generate", "create", "write", "draft"]):
            return "generation"
        elif any(keyword in task_lower for keyword in ["edit", "revise", "improve", "optimize", "rewrite"]):
            return "editing"
        elif any(keyword in task_lower for keyword in ["analyze", "review", "assess", "evaluate"]):
            return "analysis"
        else:
            # Default to generation
            return "generation"
    
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
            task_type: Type of task (generation, editing, analysis)
            context: Context for the task
            
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Extract context elements
        audience = context.get("audience", "general")
        tone = context.get("tone", "professional")
        brand_voice = context.get("brand_voice", "neutral")
        product_info = context.get("product_info", {})
        campaign_goal = context.get("campaign_goal", "inform subscribers")
        existing_content = context.get("existing_content", "")
        previous_campaigns = context.get("previous_campaigns", [])
        
        # Format shared context
        shared_context = f"""
# AUDIENCE
{audience}

# TONE & VOICE
Tone: {tone}
Brand Voice: {brand_voice}

# CAMPAIGN GOAL
{campaign_goal}

# PRODUCT/SERVICE INFORMATION
{json.dumps(product_info, indent=2) if isinstance(product_info, dict) else product_info}
"""

        # Generate system prompt based on task type
        if task_type == "generation":
            system_prompt = f"""You are a content specialist for email marketing campaigns. Your expertise lies in creating engaging, persuasive content that achieves specific marketing goals.

Your writing follows these principles:
1. Clear, concise, and focused on the value proposition
2. Action-oriented with compelling calls-to-action
3. Personalized and relevant to the target audience
4. On-brand and consistent with the company's voice and tone
5. Optimized for deliverability and engagement

When generating content, consider:
- Email subject lines should be attention-grabbing but not clickbait
- Email body content should be scannable with clear sections
- CTAs should be prominent and compelling
- Language should be benefit-focused rather than feature-focused
- Content should be GDPR-compliant and respect privacy
"""
            
            prompt = f"""# CONTENT GENERATION TASK
{task}

{shared_context}

# PREVIOUS CAMPAIGNS (for reference)
{json.dumps(previous_campaigns, indent=2) if previous_campaigns else "None available."}

# INSTRUCTIONS
Please generate high-quality content based on the task description and context provided.
Ensure the content aligns with the brand voice, resonates with the target audience, and 
supports the campaign goal.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your thought process behind the generated content",
  "content": "The generated content",
  "subject_line_options": ["Option 1", "Option 2", "Option 3"],
  "confidence": float between 0 and 1,
  "suggestions": [
    "Suggestion 1 for improving or using the content",
    "Suggestion 2 for improving or using the content"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "editing":
            system_prompt = f"""You are a content optimization specialist for email marketing campaigns. Your expertise lies in refining and improving existing content to maximize engagement and conversion.

Your editing follows these principles:
1. Enhance clarity and conciseness without losing key messages
2. Strengthen calls-to-action and persuasive elements
3. Optimize for readability and scannability
4. Ensure alignment with brand voice and target audience
5. Improve subject lines, preview text, and opening hooks

When editing content, consider:
- Maintaining the core message while improving its delivery
- Eliminating unnecessary jargon or complexity
- Enhancing the emotional appeal and benefit clarity
- Improving the visual structure and flow
- Ensuring consistency in tone throughout the content
"""
            
            prompt = f"""# CONTENT EDITING TASK
{task}

{shared_context}

# EXISTING CONTENT TO EDIT
{existing_content}

# INSTRUCTIONS
Please edit and improve the existing content based on the task description and context provided.
Focus on enhancing clarity, engagement, persuasiveness, and alignment with brand voice.
Provide both the edited content and an explanation of your changes.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your thought process behind the edits",
  "original_content": "The content before edits",
  "edited_content": "The improved content after edits",
  "key_changes": [
    "Description of key change 1",
    "Description of key change 2"
  ],
  "confidence": float between 0 and 1,
  "suggestions": [
    "Additional suggestion 1 for further improvement",
    "Additional suggestion 2 for further improvement"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "analysis":
            system_prompt = f"""You are a content analysis specialist for email marketing campaigns. Your expertise lies in evaluating content effectiveness, identifying strengths and weaknesses, and providing actionable recommendations.

Your analysis approach includes:
1. Evaluating clarity, persuasiveness, and alignment with goals
2. Identifying potential engagement and conversion obstacles
3. Analyzing tone, voice, and audience appropriateness
4. Assessing structure, readability, and call-to-action effectiveness
5. Providing specific, actionable recommendations for improvement

When analyzing content, consider:
- The content's ability to capture and maintain attention
- Clarity of value proposition and benefits
- Emotional appeal and resonance with the target audience
- Visual structure and information hierarchy
- Call-to-action clarity and compelling nature
"""
            
            prompt = f"""# CONTENT ANALYSIS TASK
{task}

{shared_context}

# CONTENT TO ANALYZE
{existing_content}

# INSTRUCTIONS
Please analyze the content based on the task description and context provided.
Evaluate its effectiveness, identify strengths and weaknesses, and provide 
detailed recommendations for improvement.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analytical approach and methodology",
  "strengths": [
    "Identified strength 1",
    "Identified strength 2"
  ],
  "weaknesses": [
    "Identified weakness 1",
    "Identified weakness 2"
  ],
  "recommendations": [
    "Specific recommendation 1",
    "Specific recommendation 2"
  ],
  "effectiveness_score": float between 0 and 10,
  "confidence": float between 0 and 1
}}
```

Respond only with the JSON object, no additional text.
"""

        else:
            # Default generic prompt
            system_prompt = f"""You are a content specialist for email marketing campaigns. Your role is to help with content creation, optimization, and analysis to maximize campaign effectiveness.

Apply your expertise to complete the requested task with high quality, considering:
- The target audience's needs and preferences
- The brand voice and tone requirements
- The specific goals of the campaign
- Best practices in email marketing content
"""
            
            prompt = f"""# CONTENT TASK
{task}

{shared_context}

# EXISTING CONTENT (if applicable)
{existing_content if existing_content else "None provided."}

# INSTRUCTIONS
Please complete the content task based on the description and context provided.
Deliver a high-quality result that meets the specific requirements of the task.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your thought process for completing this task",
  "result": "The primary output of your task",
  "confidence": float between 0 and 1,
  "additional_notes": [
    "Additional note or suggestion 1",
    "Additional note or suggestion 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        return prompt, system_prompt


# Agent factory function
def create_content_agent(agent_id: str, agent_config: Dict[str, Any]) -> ContentAgent:
    """
    Create a new content agent
    
    Args:
        agent_id: Unique identifier for this agent
        agent_config: Configuration for this agent
        
    Returns:
        ContentAgent instance
    """
    return ContentAgent(agent_id, agent_config)