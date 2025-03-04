"""
Base Agent Framework for AI Mesh Network

This module provides the abstract base class for specialized agents in the AI Mesh Network.
All agent implementations should inherit from this class.
"""

import logging
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union, ClassVar
import abc

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry

logger = logging.getLogger("ai_service.implementations.agents.base_agent")

class BaseAgent(abc.ABC):
    """Abstract base class for all AI Mesh Network agents"""
    
    # Class variables for agent type registration
    REGISTERED_TYPES: ClassVar[Dict[str, type]] = {}
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the base agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        self.agent_id = agent_id
        self.config = agent_config
        self.name = agent_config.get("name", "Generic Agent")
        self.type = agent_config.get("type", "generic")
        self.model = agent_config.get("model", "claude-3-7-sonnet")
        self.description = agent_config.get("description", "A generic AI agent")
        self.parameters = agent_config.get("parameters", {
            "temperature": 0.7,
            "max_tokens": 4000
        })
        self.capabilities = agent_config.get("capabilities", [])
        
        # Initialize LLM client
        self.llm_client = get_llm_client()
        
        # Initialize circuit breaker
        self.circuit_breaker = CircuitBreaker(
            name=f"{self.type}_agent_{agent_id[:8]}",
            failure_threshold=3,
            recovery_timeout=60.0
        )
        
        # Performance metrics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_processing_time = 0.0
        
        # State management
        self.status = "idle"
        self.last_processed_task = None
        self.task_history = []
    
    @abc.abstractmethod
    async def process_task(
        self,
        task: str,
        context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a task using this agent's capabilities
        
        Args:
            task: Task description
            context: Context for the task
            system_prompt: Optional system prompt override
            
        Returns:
            Dictionary with results
        """
        pass
    
    async def _execute_llm_with_protection(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute LLM request with circuit breaker and retry protection
        
        Args:
            prompt: Prompt for LLM
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            LLM response
        """
        # Use provided parameters or defaults from agent config
        temp = temperature if temperature is not None else self.parameters.get("temperature", 0.7)
        tokens = max_tokens if max_tokens is not None else self.parameters.get("max_tokens", 4000)
        
        # Define the actual function to execute with retry
        async def generate_text_with_retry():
            return await self.llm_client.generate_text(
                prompt=prompt,
                model=self.model,
                temperature=temp,
                max_tokens=tokens,
                system_prompt=system_prompt
            )
        
        # Define fallback function for circuit breaker
        async def fallback_generation():
            logger.warning(f"Using fallback generation for agent {self.agent_id}")
            return {
                "content": json.dumps({
                    "status": "error",
                    "error": "The service is currently experiencing issues.",
                    "message": "Unable to process request at this time. Please try again later.",
                    "confidence": 0.1
                }),
                "model": "fallback"
            }
        
        # Execute with circuit breaker and retry
        try:
            return await self.circuit_breaker.execute(
                with_retry,
                generate_text_with_retry,
                retry_count=2,
                initial_backoff=1.0,
                fallback=fallback_generation
            )
        except Exception as e:
            logger.error(f"Circuit breaker failed for agent {self.agent_id}: {e}")
            raise
    
    def process_llm_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the raw LLM result into a structured format
        
        Args:
            result: Raw LLM result
            
        Returns:
            Processed result dictionary
        """
        try:
            # Extract the content from the LLM response
            content = result.get("content", "")
            
            # Parse JSON from the content
            # Handle different JSON formats (with or without code blocks)
            try:
                # First try to parse as direct JSON
                processed = json.loads(content)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from markdown code blocks
                if "```json" in content and "```" in content.split("```json", 1)[1]:
                    json_content = content.split("```json", 1)[1].split("```", 1)[0]
                    processed = json.loads(json_content)
                elif "```" in content and "```" in content.split("```", 1)[1]:
                    json_content = content.split("```", 1)[1].split("```", 1)[0]
                    processed = json.loads(json_content)
                else:
                    # If still can't parse, return error
                    raise ValueError("Failed to parse JSON from LLM response")
            
            # Add status field if not present
            if "status" not in processed:
                processed["status"] = "success"
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing result for agent {self.agent_id}: {e}")
            logger.error(f"Raw content: {result.get('content', 'None')}")
            
            # Return error result
            return {
                "error": f"Failed to process result: {str(e)}",
                "raw_content": result.get("content", ""),
                "confidence": 0.0,
                "status": "error"
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for this agent
        
        Returns:
            Dictionary with performance metrics
        """
        success_rate = 0
        if self.total_requests > 0:
            success_rate = self.successful_requests / self.total_requests
            
        avg_processing_time = 0
        if self.successful_requests > 0:
            avg_processing_time = self.total_processing_time / self.successful_requests
            
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "agent_type": self.type,
            "status": self.status,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": success_rate,
            "total_processing_time": self.total_processing_time,
            "avg_processing_time": avg_processing_time,
            "circuit_breaker_status": self.circuit_breaker.get_stats()
        }
    
    def update_status(self, status: str) -> None:
        """
        Update the status of this agent
        
        Args:
            status: New status (idle, working, error, etc.)
        """
        self.status = status
    
    @classmethod
    def register_agent_type(cls, agent_type: str):
        """
        Decorator to register an agent type implementation
        
        Args:
            agent_type: Type identifier for this agent implementation
        
        Returns:
            Decorator function
        """
        def decorator(agent_class):
            cls.REGISTERED_TYPES[agent_type] = agent_class
            return agent_class
        return decorator
    
    @classmethod
    def create_agent(cls, agent_id: str, agent_config: Dict[str, Any]) -> 'BaseAgent':
        """
        Factory method to create an agent of the appropriate type
        
        Args:
            agent_id: Unique identifier for the agent
            agent_config: Configuration for the agent
            
        Returns:
            An instance of the appropriate agent subclass
            
        Raises:
            ValueError: If agent type is not registered
        """
        agent_type = agent_config.get("type", "generic")
        
        if agent_type not in cls.REGISTERED_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = cls.REGISTERED_TYPES[agent_type]
        return agent_class(agent_id, agent_config)


def create_agent(agent_id: str, agent_config: Dict[str, Any]) -> BaseAgent:
    """
    Create an agent of the appropriate type
    
    Args:
        agent_id: Unique identifier for the agent
        agent_config: Configuration for the agent
        
    Returns:
        An instance of the appropriate agent implementation
    """
    return BaseAgent.create_agent(agent_id, agent_config)