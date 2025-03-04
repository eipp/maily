"""
Analytics Agent for AI Mesh Network

This module implements the Analytics Agent, which specializes in analyzing campaign data,
providing insights on performance metrics, and making data-driven recommendations.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import asyncio

from ...utils.llm_client import get_llm_client
from ...utils.concurrent import CircuitBreaker, with_retry
from .base_agent import BaseAgent

logger = logging.getLogger("ai_service.implementations.agents.analytics_agent")

@BaseAgent.register_agent_type("analytics")
class AnalyticsAgent(BaseAgent):
    """Agent specialized in data analysis and performance insights"""
    
    def __init__(
        self,
        agent_id: str,
        agent_config: Dict[str, Any]
    ):
        """
        Initialize the Analytics Agent
        
        Args:
            agent_id: Unique identifier for this agent
            agent_config: Configuration for this agent
        """
        # Set default values for analytics agent
        if "name" not in agent_config:
            agent_config["name"] = "Analytics Specialist"
        
        if "type" not in agent_config:
            agent_config["type"] = "analytics"
            
        if "description" not in agent_config:
            agent_config["description"] = "Specializes in campaign performance analysis and data-driven recommendations"
            
        if "capabilities" not in agent_config:
            agent_config["capabilities"] = [
                "performance_analysis", 
                "trend_identification", 
                "audience_insights",
                "comparative_analysis",
                "predictive_recommendations"
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
        Process an analytics-related task
        
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
            logger.error(f"Analytics agent {self.agent_id} failed to process task: {e}")
            
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
                "insights": None,
                "recommendations": [],
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
        Determine the type of analytics task
        
        Args:
            task: Task description
            
        Returns:
            Task type (performance, trends, audience, comparison, prediction)
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ["performance", "metrics", "kpi", "results"]):
            return "performance"
        elif any(keyword in task_lower for keyword in ["trend", "change over time", "pattern", "historical"]):
            return "trends"
        elif any(keyword in task_lower for keyword in ["audience", "segment", "demographics", "behavior"]):
            return "audience"
        elif any(keyword in task_lower for keyword in ["compare", "comparison", "versus", "vs", "benchmark"]):
            return "comparison"
        elif any(keyword in task_lower for keyword in ["predict", "forecast", "future", "expected", "likely"]):
            return "prediction"
        else:
            # Default to performance analysis
            return "performance"
    
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
            task_type: Type of task (performance, trends, audience, comparison, prediction)
            context: Context for the task
            
        Returns:
            Tuple of (prompt, system_prompt)
        """
        # Extract context elements
        campaign_data = context.get("campaign_data", {})
        industry_benchmarks = context.get("industry_benchmarks", {})
        historical_data = context.get("historical_data", [])
        audience_segments = context.get("audience_segments", [])
        goals = context.get("goals", "")
        metrics_focus = context.get("metrics_focus", ["open_rate", "click_rate", "conversion_rate"])
        timeframe = context.get("timeframe", "last 30 days")
        
        # Format shared context
        shared_context = f"""
# CAMPAIGN DATA
{json.dumps(campaign_data, indent=2) if isinstance(campaign_data, dict) else campaign_data}

# INDUSTRY BENCHMARKS
{json.dumps(industry_benchmarks, indent=2) if isinstance(industry_benchmarks, dict) else industry_benchmarks}

# GOALS
{goals}

# METRICS FOCUS
{', '.join(metrics_focus) if isinstance(metrics_focus, list) else metrics_focus}

# TIMEFRAME
{timeframe}
"""

        # Generate system prompt based on task type
        if task_type == "performance":
            system_prompt = f"""You are an analytics specialist focusing on email marketing performance analysis. Your role is to interpret campaign metrics, identify strengths and weaknesses, and provide actionable insights to improve results.

Your performance analysis approach includes:
1. Evaluating key email metrics against goals and benchmarks
2. Identifying performance trends across campaigns
3. Highlighting successful and underperforming elements
4. Connecting metrics to business outcomes
5. Providing context-sensitive recommendations for improvement

When analyzing performance, consider:
- The relationship between different metrics (e.g., open rate to click rate)
- How performance varies across audience segments
- Technical or environmental factors that might impact results
- The specific goals of the campaign
- Industry standards and best practices
"""
            
            prompt = f"""# PERFORMANCE ANALYSIS TASK
{task}

{shared_context}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# INSTRUCTIONS
Please analyze the campaign performance based on the task description and data provided.
Evaluate key metrics against goals and benchmarks, and provide actionable insights for improvement.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis process and key observations",
  "performance_summary": "Brief overview of overall performance",
  "metrics_analysis": [
    {{
      "metric": "Metric name (e.g., 'Open Rate')",
      "value": "Current value",
      "benchmark": "Relevant benchmark",
      "assessment": "Performance assessment",
      "factors": ["Factor 1 affecting this metric", "Factor 2 affecting this metric"]
    }},
    // Additional metrics...
  ],
  "strengths": [
    "Identified strength 1",
    "Identified strength 2"
  ],
  "areas_for_improvement": [
    "Area 1 needing improvement",
    "Area 2 needing improvement"
  ],
  "recommendations": [
    {{
      "focus_area": "Area to focus on",
      "recommendation": "Specific recommendation",
      "expected_impact": "Projected impact of this change"
    }},
    // Additional recommendations...
  ],
  "confidence": float between 0 and 1,
  "next_steps": [
    "Recommended next step 1",
    "Recommended next step 2"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "trends":
            system_prompt = f"""You are an analytics specialist focusing on trend identification in email marketing data. Your role is to detect meaningful patterns over time, identify causal factors, and project future developments based on historical data.

Your trend analysis approach includes:
1. Identifying meaningful patterns in time-series data
2. Distinguishing between normal fluctuations and significant shifts
3. Connecting trend changes to campaign or external factors
4. Recognizing seasonal patterns and cyclical behaviors
5. Providing context to help interpret the significance of identified trends

When analyzing trends, consider:
- Long-term trajectories versus short-term fluctuations
- Correlation between different metrics over time
- External factors that might influence trend changes
- How trends compare to industry patterns
- The reliability of trend predictions based on data quality
"""
            
            prompt = f"""# TREND IDENTIFICATION TASK
{task}

{shared_context}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# INSTRUCTIONS
Please identify and analyze significant trends in the data based on the task description and historical information provided.
Determine patterns over time, potential causes for changes, and provide insights on future expectations.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis process and methodology",
  "identified_trends": [
    {{
      "metric": "Metric showing a trend",
      "pattern": "Description of the trend pattern",
      "timeframe": "Period over which this trend occurs",
      "magnitude": "Quantification of the trend (e.g., '15% increase')",
      "significance": "Why this trend matters"
    }},
    // Additional trends...
  ],
  "causal_factors": [
    {{
      "factor": "Factor influencing trends",
      "affected_metrics": ["Metric 1", "Metric 2"],
      "impact_description": "How this factor affects the metrics",
      "evidence": "Evidence supporting this causal relationship"
    }},
    // Additional factors...
  ],
  "forecasted_developments": [
    {{
      "metric": "Metric being forecasted",
      "forecast": "Projected future trend",
      "confidence": float between 0 and 1,
      "reasoning": "Basis for this forecast"
    }},
    // Additional forecasts...
  ],
  "confidence": float between 0 and 1,
  "recommended_monitoring": [
    "Metric or factor 1 to monitor closely",
    "Metric or factor 2 to monitor closely"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "audience":
            system_prompt = f"""You are an analytics specialist focusing on audience insights for email marketing. Your role is to analyze audience behavior, segment performance, and demographic patterns to help optimize campaign targeting and personalization.

Your audience analysis approach includes:
1. Evaluating performance metrics across different audience segments
2. Identifying high-performing and underperforming segments
3. Discovering behavioral patterns within segments
4. Recognizing opportunities for new segmentation approaches
5. Providing recommendations for segment-specific optimizations

When analyzing audience data, consider:
- How different segments respond to various content types
- Engagement patterns across the customer lifecycle
- The relationship between demographic factors and campaign performance
- Opportunities for more granular or different segmentation
- The statistical significance of segment-based observations
"""
            
            prompt = f"""# AUDIENCE INSIGHTS TASK
{task}

{shared_context}

# AUDIENCE SEGMENTS
{json.dumps(audience_segments, indent=2) if isinstance(audience_segments, list) else audience_segments}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# INSTRUCTIONS
Please analyze the audience data based on the task description and information provided.
Evaluate segment performance, identify patterns, and provide insights for audience optimization.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis methodology and approach",
  "segment_performance": [
    {{
      "segment": "Segment name or identifier",
      "key_metrics": {{
        "metric1_name": "value",
        "metric2_name": "value"
      }},
      "performance_assessment": "Assessment of this segment's performance",
      "distinctive_behaviors": ["Behavior 1", "Behavior 2"]
    }},
    // Additional segments...
  ],
  "segment_comparisons": [
    {{
      "comparison": "Description of interesting comparison",
      "difference": "Magnitude of difference",
      "significance": "Why this difference matters",
      "potential_causes": ["Potential cause 1", "Potential cause 2"]
    }},
    // Additional comparisons...
  ],
  "audience_opportunities": [
    {{
      "opportunity": "Description of opportunity",
      "target_segments": ["Segment 1", "Segment 2"],
      "recommended_approach": "How to capitalize on this opportunity",
      "potential_impact": "Estimated impact of this approach"
    }},
    // Additional opportunities...
  ],
  "segmentation_recommendations": [
    {{
      "recommendation": "Recommendation for segmentation",
      "rationale": "Why this approach would be valuable",
      "implementation_considerations": ["Consideration 1", "Consideration 2"]
    }},
    // Additional recommendations...
  ],
  "confidence": float between 0 and 1
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "comparison":
            system_prompt = f"""You are an analytics specialist focusing on comparative analysis for email marketing. Your role is to evaluate performance differences between campaigns, time periods, segments, or against industry benchmarks to derive actionable insights.

Your comparative analysis approach includes:
1. Identifying significant performance differentials across comparison points
2. Determining potential causes for observed differences
3. Extracting lessons from high-performing examples
4. Contextualizing performance within broader trends
5. Recommending strategies based on comparative findings

When conducting comparative analysis, consider:
- Statistical significance of observed differences
- Contributing factors to performance variations
- Contextual elements that may affect fair comparison
- Methodological considerations when comparing different types of data
- How insights from comparisons can inform future strategy
"""
            
            prompt = f"""# COMPARATIVE ANALYSIS TASK
{task}

{shared_context}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# INDUSTRY BENCHMARKS
{json.dumps(industry_benchmarks, indent=2) if isinstance(industry_benchmarks, dict) else industry_benchmarks}

# INSTRUCTIONS
Please conduct a comparative analysis based on the task description and data provided.
Identify significant differences, determine causes, and provide insights based on the comparison.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis approach and methodology",
  "comparison_summary": "Overview of the comparison and key findings",
  "detailed_comparisons": [
    {{
      "comparison_points": ["Point A", "Point B"],
      "metrics": [
        {{
          "metric": "Metric name",
          "values": {{
            "point_a": "Value for Point A",
            "point_b": "Value for Point B"
          }},
          "difference": "Absolute and percentage difference",
          "significance": "Statistical or practical significance of this difference"
        }},
        // Additional metrics...
      ],
      "key_differences": [
        "Notable difference 1",
        "Notable difference 2"
      ],
      "potential_causes": [
        "Potential cause 1 for differences",
        "Potential cause 2 for differences"
      ]
    }},
    // Additional comparison sets...
  ],
  "learnings": [
    {{
      "learning": "Key learning from comparison",
      "supporting_evidence": "Evidence supporting this learning",
      "applicability": "How this learning can be applied"
    }},
    // Additional learnings...
  ],
  "recommendations": [
    {{
      "recommendation": "Recommendation based on comparison",
      "rationale": "Why this is recommended",
      "implementation_approach": "How to implement this recommendation"
    }},
    // Additional recommendations...
  ],
  "confidence": float between 0 and 1
}}
```

Respond only with the JSON object, no additional text.
"""

        elif task_type == "prediction":
            system_prompt = f"""You are an analytics specialist focusing on predictive recommendations for email marketing. Your role is to forecast future performance, identify potential opportunities or risks, and recommend proactive strategies.

Your predictive analysis approach includes:
1. Using historical data to project future performance
2. Identifying factors likely to influence upcoming results
3. Assessing the probability of various outcomes
4. Providing confidence levels for predictions
5. Recommending actions to optimize future performance

When making predictions, consider:
- The quality and quantity of historical data available
- Seasonal factors and cyclical patterns
- Market trends and industry developments
- The impact of planned changes or interventions
- Multiple scenarios based on different assumptions
"""
            
            prompt = f"""# PREDICTIVE RECOMMENDATIONS TASK
{task}

{shared_context}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# INSTRUCTIONS
Please provide predictive analysis and recommendations based on the task description and historical data provided.
Forecast future performance, identify opportunities and risks, and recommend proactive strategies.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your predictive analysis methodology and approach",
  "performance_forecasts": [
    {{
      "metric": "Metric being forecasted",
      "current_value": "Current value of this metric",
      "forecasted_value": "Predicted future value",
      "timeframe": "Timeframe for this prediction",
      "confidence": float between 0 and 1,
      "influencing_factors": [
        "Factor 1 influencing this forecast",
        "Factor 2 influencing this forecast"
      ]
    }},
    // Additional forecasts...
  ],
  "opportunity_predictions": [
    {{
      "opportunity": "Predicted opportunity",
      "impact_potential": "Estimated potential impact",
      "probability": float between 0 and 1,
      "recommended_actions": [
        "Action 1 to capitalize on this opportunity",
        "Action 2 to capitalize on this opportunity"
      ]
    }},
    // Additional opportunities...
  ],
  "risk_predictions": [
    {{
      "risk": "Predicted risk",
      "potential_impact": "Estimated potential impact",
      "probability": float between 0 and 1,
      "mitigation_strategies": [
        "Strategy 1 to mitigate this risk",
        "Strategy 2 to mitigate this risk"
      ]
    }},
    // Additional risks...
  ],
  "scenario_analysis": [
    {{
      "scenario": "Possible future scenario",
      "probability": float between 0 and 1,
      "implications": [
        "Implication 1 of this scenario",
        "Implication 2 of this scenario"
      ],
      "recommended_preparation": "How to prepare for this scenario"
    }},
    // Additional scenarios...
  ],
  "confidence": float between 0 and 1,
  "limitations": [
    "Limitation 1 of this predictive analysis",
    "Limitation 2 of this predictive analysis"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        else:
            # Default generic prompt
            system_prompt = f"""You are an analytics specialist for email marketing campaigns. Your role is to provide data-driven insights and recommendations to improve campaign performance and achieve business goals.

Apply your expertise to complete the requested task with high quality, considering:
- The available campaign performance data
- Historical trends and patterns
- Industry benchmarks and best practices
- The specific goals of the campaign
- The target audience and segmentation
"""
            
            prompt = f"""# ANALYTICS TASK
{task}

{shared_context}

# HISTORICAL DATA
{json.dumps(historical_data, indent=2) if isinstance(historical_data, list) else historical_data}

# AUDIENCE SEGMENTS
{json.dumps(audience_segments, indent=2) if isinstance(audience_segments, list) else audience_segments}

# INSTRUCTIONS
Please complete the analytics task based on the description and data provided.
Deliver high-quality insights and recommendations that meet the specific requirements of the task.

# RESPONSE FORMAT
Respond in JSON format with the following structure:
```json
{{
  "reasoning": "Your analysis approach and methodology",
  "insights": [
    "Key insight 1 from the analysis",
    "Key insight 2 from the analysis"
  ],
  "data_interpretation": "Your interpretation of the data",
  "recommendations": [
    {{
      "recommendation": "Specific recommendation",
      "rationale": "Why you're recommending this",
      "expected_impact": "Projected impact of this recommendation"
    }},
    // Additional recommendations...
  ],
  "confidence": float between 0 and 1,
  "limitations": [
    "Limitation 1 of this analysis",
    "Limitation 2 of this analysis"
  ]
}}
```

Respond only with the JSON object, no additional text.
"""

        return prompt, system_prompt


# Agent factory function
def create_analytics_agent(agent_id: str, agent_config: Dict[str, Any]) -> AnalyticsAgent:
    """
    Create a new analytics agent
    
    Args:
        agent_id: Unique identifier for this agent
        agent_config: Configuration for this agent
        
    Returns:
        AnalyticsAgent instance
    """
    return AnalyticsAgent(agent_id, agent_config)