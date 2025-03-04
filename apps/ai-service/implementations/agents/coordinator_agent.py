"""
Coordinator Agent for AI Mesh Network

This module implements the Coordinator Agent, which orchestrates the work of specialized agents,
delegates tasks, aggregates results, and manages the overall AI workflow in the mesh network.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry
from .base_agent import BaseAgent

logger = logging.getLogger("ai_service.implementations.agents.coordinator_agent")

@BaseAgent.register_agent_type("coordinator")
class CoordinatorAgent(BaseAgent):
    """Agent specialized in coordinating multiple specialized agents"""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the Coordinator Agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        # Set default values for coordinator agent
        if "name" not in agent_config:
            agent_config["name"] = "Orchestration Coordinator"
        
        if "type" not in agent_config:
            agent_config["type"] = "coordinator"
            
        if "description" not in agent_config:
            agent_config["description"] = "Orchestrates specialized agents, delegates tasks, and aggregates results"
            
        if "capabilities" not in agent_config:
            agent_config["capabilities"] = [
                "task_delegation", 
                "result_aggregation", 
                "workflow_management",
                "agent_selection",
                "conflict_resolution"
            ]
        
        # Initialize base agent
        super().__init__(agent_id, agent_config)
        
        # Specialized fields for coordinator
        self.available_agents = agent_config.get("available_agents", {})
        self.active_workflows = {}
        self.completed_workflows = []
    
    async def process_task(
        self,
        task: str,
        context: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a coordination task
        
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
            
            # For delegation tasks, extract the delegation plan for further processing
            if task_type == "delegation" and "delegation_plan" in processed_result:
                # Store the delegation plan for future reference
                workflow_id = f"workflow_{int(time.time())}_{self.total_requests}"
                self.active_workflows[workflow_id] = {
                    "task": task,
                    "task_type": task_type,
                    "plan": processed_result["delegation_plan"],
                    "status": "created",
                    "created_at": time.time(),
                    "results": {},
                    "completion": 0.0  # Percentage complete
                }
                processed_result["workflow_id"] = workflow_id
            
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
            logger.error(f"Coordinator agent {self.agent_id} failed to process task: {e}")
            
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
                "delegation_plan": None,
                "aggregate_results": None,
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
        Determine the type of coordination task
        
        Args:
            task: Task description
            
        Returns:
            Task type (delegation, aggregation, workflow, selection, resolution)
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["delegate", "assign", "distribute", "allocate"]):
            return "delegation"
        elif any(keyword in task_lower for keyword in ["aggregate", "combine", "consolidate", "merge", "summarize"]):
            return "aggregation"
        elif any(keyword in task_lower for keyword in ["workflow", "process", "sequence", "pipeline"]):
            return "workflow"
        elif any(keyword in task_lower for keyword in ["select", "choose", "pick", "identify best"]):
            return "selection"
        elif any(keyword in task_lower for keyword in ["resolve", "conflict", "reconcile", "inconsistency"]):
            return "resolution"
        else:
            # Default to task delegation
            return "delegation"
    
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
            task_type: Type of task (delegation, aggregation, workflow, selection, resolution)
            context: Context for the task
            
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Extract context elements
        available_agents = context.get("available_agents", self.available_agents)
        campaign_data = context.get("campaign_data", {})
        user_request = context.get("user_request", "")
        workflow_id = context.get("workflow_id", "")
        agent_results = context.get("agent_results", {})
        priorities = context.get("priorities", {})
        
        # Format available agents info
        available_agents_str = ""
        for agent_type, agents in available_agents.items():
            available_agents_str += f"## {agent_type.upper()} AGENTS\n"
            for agent in agents:
                capabilities = ", ".join(agent.get("capabilities", []))
                available_agents_str += f"- {agent.get('name', 'Unnamed Agent')} (ID: {agent.get('id', 'unknown')})\n"
                available_agents_str += f"  Capabilities: {capabilities}\n"
        
        # Format shared context
        shared_context = f"""
# AVAILABLE AGENTS
{available_agents_str if available_agents_str else "No specialized agents available."}

# USER REQUEST
{user_request}

# PRIORITIES
{json.dumps(priorities, indent=2) if isinstance(priorities, dict) else priorities}
"""

        # Generate system prompt based on task type
        if task_type == "delegation":
            system_prompt = f"""You are a coordination specialist for an AI Mesh Network. Your role is to analyze complex tasks, break them down into subtasks, and delegate them to specialized agents based on their capabilities.

Your task delegation approach includes:
1. Analyzing the task to identify different components requiring specialized expertise
2. Matching subtasks to agent capabilities for optimal execution
3. Determining the most efficient sequence for subtask execution
4. Creating clear, specific instructions for each agent
5. Ensuring all aspects of the original task are covered by the delegation plan

When delegating tasks, consider:
- The specific strengths and limitations of each available agent
- Dependencies between subtasks
- Parallelization opportunities for efficiency
- The priority of different aspects of the task
- Contingency plans for potential agent failures
"""
            
            prompt = f"""# TASK DELEGATION ASSIGNMENT
{task}

{shared_context}

# CAMPAIGN DATA
{json.dumps(campaign_data, indent=2) if isinstance(campaign_data, dict) else campaign_data}

# INSTRUCTIONS
Please analyze the task and create a comprehensive delegation plan.
Identify appropriate specialized agents for each subtask and determine the optimal execution order.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of the task and delegation approach",
  "delegation_plan": [
    {{
      "subtask_id": "Unique identifier for this subtask",
      "description": "Clear description of what needs to be done",
      "assigned_agent_type": "Type of agent best suited for this task",
      "assigned_agent_id": "Specific agent ID if applicable, otherwise null",
      "required_capabilities": ["capability1", "capability2"],
      "dependencies": ["subtask_id_1", "subtask_id_2"],
      "priority": integer from 1-5 (1 highest),
      "estimated_complexity": integer from 1-5 (5 most complex)
    }},
    // Additional subtasks...
  ],
  "execution_sequence": [
    ["subtask_id_1", "subtask_id_2"],  // Tasks that can run in parallel
    ["subtask_id_3"],  // Tasks that depend on previous batch
    // Additional sequences...
  ],
  "fallback_options": [
    {{
      "subtask_id": "ID of task that might need fallback",
      "alternative_agent_types": ["type1", "type2"]
    }},
    // Additional fallbacks...
  ],
  "confidence": float between 0 and 1,
  "estimated_completion_time": "Estimated time to complete all tasks"
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "aggregation":
            system_prompt = f"""You are a results aggregation specialist for an AI Mesh Network. Your role is to combine outputs from multiple specialized agents into a cohesive, integrated result that addresses the original user request.

Your results aggregation approach includes:
1. Analyzing outputs from different agents to identify key insights
2. Resolving conflicts or inconsistencies between agent outputs
3. Synthesizing information into a unified, coherent response
4. Prioritizing information based on relevance to the original request
5. Ensuring all critical information is retained while eliminating redundancy

When aggregating results, consider:
- The relative confidence levels of different agents' outputs
- The coherence of the integrated result
- The original user's intent and priorities
- Potential gaps in the collective agent responses
- Opportunities to derive additional insights from the combined results
"""
            
            prompt = f"""# RESULTS AGGREGATION TASK
{task}

{shared_context}

# AGENT RESULTS
{json.dumps(agent_results, indent=2) if isinstance(agent_results, dict) else agent_results}

# INSTRUCTIONS
Please aggregate the results from the specialized agents into a cohesive, integrated response.
Resolve any conflicts, eliminate redundancies, and ensure the result addresses the original request.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to aggregating these results",
  "aggregate_result": {{
    // Combined output addressing the original request
    // Structure depends on the specific task
  }},
  "key_insights": [
    "Important insight 1 from aggregated results",
    "Important insight 2 from aggregated results"
  ],
  "conflicts_resolved": [
    {{
      "conflict": "Description of conflict between agent outputs",
      "resolution": "How the conflict was resolved",
      "rationale": "Reasoning behind this resolution approach"
    }},
    // Additional resolved conflicts...
  ],
  "confidence": float between 0 and 1,
  "information_gaps": [
    "Identified gap 1 in the collective agent responses",
    "Identified gap 2 in the collective agent responses"
  ],
  "additional_recommendations": [
    "Recommendation 1 based on aggregated insights",
    "Recommendation 2 based on aggregated insights"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "workflow":
            system_prompt = f"""You are a workflow management specialist for an AI Mesh Network. Your role is to design, monitor, and optimize multi-agent workflows to efficiently accomplish complex tasks.

Your workflow management approach includes:
1. Designing logical, efficient processes for multi-step tasks
2. Monitoring the progress and performance of active workflows
3. Making real-time adjustments based on intermediate results
4. Managing resource allocation and agent utilization
5. Identifying optimization opportunities in workflow patterns

When managing workflows, consider:
- The dependencies between different workflow stages
- Critical path identification and bottleneck prevention
- Opportunities for parallel processing
- Exception handling and recovery strategies
- Balancing thoroughness with efficiency
"""
            
            prompt = f"""# WORKFLOW MANAGEMENT TASK
{task}

{shared_context}

# CAMPAIGN DATA
{json.dumps(campaign_data, indent=2) if isinstance(campaign_data, dict) else campaign_data}

# ACTIVE WORKFLOW
{workflow_id if workflow_id else "No specific workflow ID provided."}

# INSTRUCTIONS
Please design, monitor, or optimize the workflow as requested in the task description.
Create a clear process that efficiently coordinates multiple specialized agents.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis and approach to this workflow task",
  "workflow_plan": [
    {{
      "stage": "Stage name or number",
      "description": "What happens in this stage",
      "agent_types": ["agent_type1", "agent_type2"],
      "expected_outputs": ["output1", "output2"],
      "success_criteria": "Criteria for successful completion",
      "contingency": "Action to take if stage fails"
    }},
    // Additional stages...
  ],
  "dependencies": [
    {{
      "dependent_stage": "Stage that depends on another",
      "dependency": "Stage it depends on",
      "dependency_type": "full/partial"
    }},
    // Additional dependencies...
  ],
  "performance_monitoring": [
    {{
      "metric": "Metric to monitor",
      "threshold": "Threshold for intervention",
      "action": "Action to take if threshold is crossed"
    }},
    // Additional monitoring points...
  ],
  "optimization_opportunities": [
    "Identified optimization 1",
    "Identified optimization 2"
  ],
  "confidence": float between 0 and 1,
  "estimated_efficiency_gain": "Projected improvement from optimizations"
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "selection":
            system_prompt = f"""You are an agent selection specialist for an AI Mesh Network. Your role is to identify the most appropriate specialized agents for specific tasks based on their capabilities, performance history, and current availability.

Your agent selection approach includes:
1. Analyzing task requirements to identify needed capabilities
2. Evaluating agent performance metrics and success rates
3. Considering agent specializations and domain expertise
4. Balancing workload distribution across available agents
5. Prioritizing agents based on task-specific suitability

When selecting agents, consider:
- The specific skills and knowledge required for the task
- Recent performance metrics for relevant agents
- Current agent load and availability
- The complexity and priority of the task
- Potential agent combinations for complex tasks
"""
            
            prompt = f"""# AGENT SELECTION TASK
{task}

{shared_context}

# TASK DETAILS
{user_request}

# INSTRUCTIONS
Please select the most appropriate agent(s) for the specified task based on capabilities and performance.
Provide clear reasoning for your selection and any recommended agent configurations.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of task requirements and agent selection approach",
  "selected_agents": [
    {{
      "agent_type": "Type of selected agent",
      "agent_id": "Specific agent ID if applicable",
      "primary_responsibility": "What this agent should focus on",
      "required_capabilities": ["capability1", "capability2"],
      "selection_factors": [
        "Factor 1 that led to selecting this agent",
        "Factor 2 that led to selecting this agent"
      ]
    }},
    // Additional agents if needed...
  ],
  "alternative_options": [
    {{
      "agent_type": "Alternative agent type",
      "agent_id": "Specific agent ID if applicable",
      "strengths": ["Strength 1", "Strength 2"],
      "limitations": ["Limitation 1", "Limitation 2"]
    }},
    // Additional alternatives...
  ],
  "recommended_configuration": {{
    "execution_mode": "sequential/parallel/hybrid",
    "communication_pattern": "How selected agents should communicate",
    "result_integration": "How outputs should be combined"
  }},
  "confidence": float between 0 and 1,
  "performance_expectations": "Expected outcomes with this selection"
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "resolution":
            system_prompt = f"""You are a conflict resolution specialist for an AI Mesh Network. Your role is to reconcile differences, inconsistencies, or contradictions in outputs from different specialized agents to produce coherent final results.

Your conflict resolution approach includes:
1. Identifying conflicts in information, recommendations, or approaches
2. Analyzing the underlying causes of conflicts
3. Weighing the credibility and confidence of conflicting outputs
4. Developing resolution strategies based on task priorities
5. Documenting resolution decisions for transparency

When resolving conflicts, consider:
- The confidence levels expressed by each agent
- The core expertise areas of conflicting agents
- Potential synthesis opportunities that incorporate multiple perspectives
- The original user intent and priorities
- Opportunities to gather additional information to resolve conflicts
"""
            
            prompt = f"""# CONFLICT RESOLUTION TASK
{task}

{shared_context}

# AGENT RESULTS
{json.dumps(agent_results, indent=2) if isinstance(agent_results, dict) else agent_results}

# INSTRUCTIONS
Please identify and resolve conflicts between the specialized agent outputs.
Develop a coherent final result that addresses inconsistencies while preserving valuable insights.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis of conflicts and resolution approach",
  "identified_conflicts": [
    {{
      "conflict_id": "Unique identifier for this conflict",
      "description": "Clear description of the conflict",
      "agents_involved": ["agent_1", "agent_2"],
      "severity": "High/Medium/Low",
      "impact": "How this conflict affects the overall result"
    }},
    // Additional conflicts...
  ],
  "resolution_strategies": [
    {{
      "conflict_id": "ID of conflict being resolved",
      "resolution_approach": "Strategy used to resolve this conflict",
      "rationale": "Reasoning behind this resolution approach",
      "resolved_output": "The reconciled output for this conflict"
    }},
    // Additional resolutions...
  ],
  "integrated_result": {{
    // Fully reconciled output addressing the original request
    // Structure depends on the specific task
  }},
  "confidence": float between 0 and 1,
  "unresolved_issues": [
    "Issue 1 that couldn't be fully resolved",
    "Issue 2 that couldn't be fully resolved"
  ],
  "recommendations": [
    "Recommendation 1 based on conflict analysis",
    "Recommendation 2 based on conflict analysis"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        else:
            # Default generic prompt
            system_prompt = f"""You are a coordination specialist for an AI Mesh Network. Your role is to orchestrate specialized agents, delegate tasks, and integrate results to effectively address complex user requests.

Apply your expertise to complete the requested task with high quality, considering:
- The specialized capabilities of different agent types
- Efficient workflow design and execution
- Optimal integration of multiple agent outputs
- Balance between thoroughness and efficiency
- The original user intent and priorities
"""
            
            prompt = f"""# COORDINATION TASK
{task}

{shared_context}

# CAMPAIGN DATA
{json.dumps(campaign_data, indent=2) if isinstance(campaign_data, dict) else campaign_data}

# AGENT RESULTS
{json.dumps(agent_results, indent=2) if isinstance(agent_results, dict) else agent_results}

# INSTRUCTIONS
Please complete the coordination task based on the description and context provided.
Deliver high-quality orchestration that effectively utilizes the specialized agents.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your approach to this coordination task",
  "coordination_solution": "The core output of your coordination work",
  "key_decisions": [
    {{
      "decision": "Important coordination decision made",
      "rationale": "Reasoning behind this decision",
      "impact": "How this affects the overall result"
    }},
    // Additional decisions...
  ],
  "agent_utilization": [
    {{
      "agent_type": "Type of agent utilized",
      "purpose": "How this agent was used",
      "value_added": "Specific contribution to the result"
    }},
    // Additional agents...
  ],
  "confidence": float between 0 and 1,
  "recommendations": [
    "Recommendation 1 for future coordination",
    "Recommendation 2 for future coordination"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        return prompt, system_prompt

    async def update_workflow_status(
        self,
        workflow_id: str,
        subtask_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a subtask in a workflow
        
        Args:
            workflow_id: ID of the workflow
            subtask_id: ID of the subtask to update
            status: New status (in_progress, completed, failed)
            result: Optional result data
            
        Returns:
            Updated workflow status
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
            
        workflow = self.active_workflows[workflow_id]
        
        # Find the subtask
        subtask_found = False
        for subtask in workflow["plan"]:
            if subtask["subtask_id"] == subtask_id:
                subtask["status"] = status
                subtask["updated_at"] = time.time()
                if result is not None:
                    subtask["result"] = result
                subtask_found = True
                break
                
        if not subtask_found:
            raise ValueError(f"Subtask {subtask_id} not found in workflow {workflow_id}")
            
        # Update overall workflow status and completion
        total_subtasks = len(workflow["plan"])
        completed_subtasks = sum(1 for subtask in workflow["plan"] if subtask.get("status") == "completed")
        failed_subtasks = sum(1 for subtask in workflow["plan"] if subtask.get("status") == "failed")
        
        workflow["completion"] = (completed_subtasks + failed_subtasks) / total_subtasks
        
        # Check if all subtasks are complete
        if workflow["completion"] >= 1.0:
            workflow["status"] = "completed"
            workflow["completed_at"] = time.time()
            # Move to completed workflows
            self.completed_workflows.append(workflow)
            del self.active_workflows[workflow_id]
        elif failed_subtasks > 0:
            workflow["status"] = "partial"
        else:
            workflow["status"] = "in_progress"
            
        return workflow

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get the current status of a workflow
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status information
        """
        # Check active workflows first
        if workflow_id in self.active_workflows:
            return self.active_workflows[workflow_id]
            
        # Then check completed workflows
        for workflow in self.completed_workflows:
            if workflow.get("workflow_id") == workflow_id:
                return workflow
                
        raise ValueError(f"Workflow {workflow_id} not found")

    def get_agent_workload(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get workload statistics for agents
        
        Args:
            agent_type: Optional filter for specific agent type
            
        Returns:
            Dictionary with workload statistics
        """
        agent_stats = {}
        
        # Count tasks assigned to each agent across active workflows
        for workflow_id, workflow in self.active_workflows.items():
            for subtask in workflow["plan"]:
                task_agent_type = subtask.get("assigned_agent_type")
                task_agent_id = subtask.get("assigned_agent_id")
                
                if agent_type is not None and task_agent_type != agent_type:
                    continue
                    
                if task_agent_type not in agent_stats:
                    agent_stats[task_agent_type] = {
                        "total_tasks": 0,
                        "in_progress": 0,
                        "completed": 0,
                        "failed": 0,
                        "agents": {}
                    }
                    
                agent_stats[task_agent_type]["total_tasks"] += 1
                
                status = subtask.get("status", "pending")
                if status == "in_progress":
                    agent_stats[task_agent_type]["in_progress"] += 1
                elif status == "completed":
                    agent_stats[task_agent_type]["completed"] += 1
                elif status == "failed":
                    agent_stats[task_agent_type]["failed"] += 1
                    
                if task_agent_id:
                    if task_agent_id not in agent_stats[task_agent_type]["agents"]:
                        agent_stats[task_agent_type]["agents"][task_agent_id] = {
                            "total_tasks": 0,
                            "in_progress": 0,
                            "completed": 0,
                            "failed": 0
                        }
                        
                    agent_stats[task_agent_type]["agents"][task_agent_id]["total_tasks"] += 1
                    
                    if status == "in_progress":
                        agent_stats[task_agent_type]["agents"][task_agent_id]["in_progress"] += 1
                    elif status == "completed":
                        agent_stats[task_agent_type]["agents"][task_agent_id]["completed"] += 1
                    elif status == "failed":
                        agent_stats[task_agent_type]["agents"][task_agent_id]["failed"] += 1
                        
        return agent_stats


# Agent factory function
def create_coordinator_agent(agent_id: str, agent_config: Dict[str, Any]) -> CoordinatorAgent:
    """
    Create a new coordinator agent
    
    Args:
        agent_id: Unique identifier for this agent
        agent_config: Configuration for this agent
        
    Returns:
        CoordinatorAgent instance
    """
    return CoordinatorAgent(agent_id, agent_config)