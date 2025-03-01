from typing import Dict, List, Any, Optional, Union, Tuple, Set
import asyncio
import json
import httpx
import uuid
from loguru import logger
from datetime import datetime
import openai
from enum import Enum, auto

from ..config.settings import get_settings
from ..cache.redis_client import get_redis_client

# Global instance
_ai_orchestrator_instance = None

async def get_ai_orchestrator():
    """Get or create the global AI Orchestrator instance"""
    global _ai_orchestrator_instance

    if _ai_orchestrator_instance is None:
        _ai_orchestrator_instance = AIOrchestrator()
        await _ai_orchestrator_instance.initialize()

    return _ai_orchestrator_instance

class AgentRole(str, Enum):
    COORDINATOR = "coordinator"
    DESIGNER = "designer"
    ANALYST = "analyst"
    WRITER = "writer"
    RESEARCHER = "researcher"
    REVIEWER = "reviewer"

class ThoughtType(str, Enum):
    INITIAL = "initial"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    CRITICAL = "critical"
    QUERY = "query"
    RESPONSE = "response"
    DECISION = "decision"
    CONCLUSION = "conclusion"
    SUMMARY = "summary"

class AgentThought:
    """Represents a thought from an AI agent with chain-of-thought reasoning"""

    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        thought_id: str,
        content: str,
        thought_type: str,
        canvas_id: str,
        timestamp: Optional[datetime] = None,
        references: Optional[List[str]] = None,
        parent_thought_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 0.0,
        visual_position: Optional[Dict[str, float]] = None
    ):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.thought_id = thought_id
        self.content = content
        self.thought_type = thought_type
        self.canvas_id = canvas_id
        self.timestamp = timestamp or datetime.utcnow()
        self.references = references or []
        self.parent_thought_id = parent_thought_id
        self.metadata = metadata or {}
        self.confidence = confidence
        self.visual_position = visual_position or {"x": 0, "y": 0}

    def to_dict(self) -> Dict[str, Any]:
        """Convert thought to dictionary for storage/transmission"""
        return {
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "thought_id": self.thought_id,
            "content": self.content,
            "thought_type": self.thought_type,
            "canvas_id": self.canvas_id,
            "timestamp": self.timestamp.isoformat(),
            "references": self.references,
            "parent_thought_id": self.parent_thought_id,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "visual_position": self.visual_position
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentThought':
        """Create thought from dictionary"""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            agent_id=data["agent_id"],
            agent_role=data["agent_role"],
            thought_id=data["thought_id"],
            content=data["content"],
            thought_type=data["thought_type"],
            canvas_id=data["canvas_id"],
            timestamp=timestamp,
            references=data.get("references", []),
            parent_thought_id=data.get("parent_thought_id"),
            metadata=data.get("metadata", {}),
            confidence=data.get("confidence", 0.0),
            visual_position=data.get("visual_position", {"x": 0, "y": 0})
        )

    def to_json(self) -> str:
        """Convert thought to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'AgentThought':
        """Create thought instance from JSON string"""
        return cls.from_dict(json.loads(json_str))

class AIAgent:
    """Represents an AI agent with a specific role that can contribute thoughts"""

    def __init__(
        self,
        agent_id: str,
        role: str,
        name: str,
        orchestrator: 'AIOrchestrator',
        model: str = "gpt-4o",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id
        self.role = role
        self.name = name
        self.orchestrator = orchestrator
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.metadata = metadata or {}
        self.thoughts: List[AgentThought] = []

    async def generate_thought(
        self,
        prompt: str,
        thought_type: str,
        canvas_id: str,
        parent_thought_id: Optional[str] = None,
        references: Optional[List[str]] = None,
        visual_position: Optional[Dict[str, float]] = None
    ) -> AgentThought:
        """Generate a new thought based on the prompt"""
        try:
            # Enhance prompt with role-specific context
            role_context = self._get_role_context()
            enhanced_prompt = f"{role_context}\n\n{prompt}"

            # Call AI model
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are an AI agent with the role of {self.role}. {role_context}"},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            # Extract content
            content = response.choices[0].message.content

            # Create thought
            thought_id = f"thought_{uuid.uuid4()}"
            thought = AgentThought(
                agent_id=self.agent_id,
                agent_role=self.role,
                thought_id=thought_id,
                content=content,
                thought_type=thought_type,
                canvas_id=canvas_id,
                references=references or [],
                parent_thought_id=parent_thought_id,
                visual_position=visual_position,
                confidence=self._estimate_confidence(content)
            )

            # Save thought
            self.thoughts.append(thought)

            # Publish thought to orchestrator
            await self.orchestrator.publish_thought(thought)

            return thought

        except Exception as e:
            logger.error(f"Error generating thought for agent {self.agent_id}: {e}")
            # Create error thought
            thought_id = f"thought_{uuid.uuid4()}"
            thought = AgentThought(
                agent_id=self.agent_id,
                agent_role=self.role,
                thought_id=thought_id,
                content=f"Error generating thought: {str(e)}",
                thought_type=ThoughtType.ERROR,
                canvas_id=canvas_id,
                parent_thought_id=parent_thought_id,
                visual_position=visual_position,
                confidence=0.0
            )
            self.thoughts.append(thought)
            await self.orchestrator.publish_thought(thought)
            return thought

    def _get_role_context(self) -> str:
        """Get context specific to this agent's role"""
        role_contexts = {
            AgentRole.COORDINATOR: "You coordinate activities between different agents, synthesize information, and ensure coherent progress. You help make final decisions based on input from other agents.",
            AgentRole.DESIGNER: "You focus on visual design aspects, layout, colors, and aesthetics. You suggest improvements to make content visually appealing and effective.",
            AgentRole.ANALYST: "You analyze data, identify patterns, and provide insights. You help interpret information critically and make evidence-based recommendations.",
            AgentRole.WRITER: "You craft clear, compelling copy and content. You help improve text for clarity, engagement, and persuasiveness.",
            AgentRole.RESEARCHER: "You gather information, identify relevant sources, and synthesize findings. You help expand knowledge on specific topics.",
            AgentRole.REVIEWER: "You critically evaluate content, identify issues, and suggest improvements. You help ensure quality and coherence."
        }

        return role_contexts.get(self.role, "You are an AI assistant helping with tasks.")

    def _estimate_confidence(self, content: str) -> float:
        """Estimate confidence level based on content analysis"""
        # Simple heuristic - could be improved with more sophisticated analysis
        confidence = 0.7  # Default medium-high confidence

        hedging_phrases = ["perhaps", "maybe", "might", "could be", "possibly", "I think", "I believe", "not sure"]
        certainty_phrases = ["definitely", "certainly", "absolutely", "without doubt", "clearly", "obviously"]

        # Lower confidence for each hedging phrase
        for phrase in hedging_phrases:
            if phrase.lower() in content.lower():
                confidence -= 0.1

        # Increase confidence for each certainty phrase
        for phrase in certainty_phrases:
            if phrase.lower() in content.lower():
                confidence += 0.1

        # Clamp between 0.1 and 1.0
        return max(0.1, min(1.0, confidence))

class AIOrchestrator:
    """Orchestrates multiple AI agents for collaborative thinking"""

    def __init__(self):
        self.agents_by_canvas: Dict[str, Dict[str, AIAgent]] = {}
        self.thought_cache: Dict[str, Dict[str, AgentThought]] = {}  # canvas_id -> thought_id -> thought
        self.thought_relations: Dict[str, Dict[str, Set[str]]] = {}  # canvas_id -> parent_id -> set of child_ids
        self.redis = None
        self.settings = get_settings()
        self.lock = asyncio.Lock()

    async def initialize(self):
        """Initialize the orchestrator with resources"""
        self.redis = await get_redis_client()
        settings = get_settings()
        logger.info("AI Orchestrator initialized")

    async def create_agent(
        self,
        role: str,
        name: Optional[str] = None,
        model: str = "gpt-4o"
    ) -> AIAgent:
        """Create a new agent with the specified role"""
        agent_id = f"agent_{uuid.uuid4()}"
        name = name or f"{role.capitalize()} Agent"

        agent = AIAgent(
            agent_id=agent_id,
            role=role,
            name=name,
            orchestrator=self,
            model=model
        )

        if role not in self.agents_by_canvas:
            self.agents_by_canvas[role] = {}
        self.agents_by_canvas[role][agent_id] = agent
        return agent

    async def get_agent(self, agent_id: str) -> Optional[AIAgent]:
        """Get an agent by ID"""
        for role, agents in self.agents_by_canvas.items():
            if agent_id in agents:
                return agents[agent_id]
        return None

    async def initialize_standard_team(self, canvas_id: str) -> Dict[str, AIAgent]:
        """Create a standard team of agents for a canvas"""
        team = {}

        # Create agents for each role
        team["coordinator"] = await self.create_agent(AgentRole.COORDINATOR, "Coordination Agent")
        team["designer"] = await self.create_agent(AgentRole.DESIGNER, "Design Agent")
        team["analyst"] = await self.create_agent(AgentRole.ANALYST, "Analysis Agent")
        team["writer"] = await self.create_agent(AgentRole.WRITER, "Content Agent")
        team["researcher"] = await self.create_agent(AgentRole.RESEARCHER, "Research Agent")
        team["reviewer"] = await self.create_agent(AgentRole.REVIEWER, "Review Agent")

        # Initialize empty thought collections for this canvas
        self.thought_cache[canvas_id] = {}
        self.thought_relations[canvas_id] = {}

        return team

    async def publish_thought(self, thought: AgentThought):
        """Publish a thought to the collective knowledge and notify clients"""
        async with self.lock:
            # Save thought to canvas collection
            if thought.canvas_id not in self.thought_cache:
                self.thought_cache[thought.canvas_id] = {}

            self.thought_cache[thought.canvas_id][thought.thought_id] = thought

            # Update thought tree
            if thought.parent_thought_id:
                if thought.parent_thought_id not in self.thought_relations[thought.canvas_id]:
                    self.thought_relations[thought.canvas_id][thought.parent_thought_id] = set()

                self.thought_relations[thought.canvas_id][thought.parent_thought_id].add(thought.thought_id)

        # Publish to Redis for clients
        if self.redis:
            channel = f"canvas:thoughts:{thought.canvas_id}"
            await self.redis.publish(channel, json.dumps(thought.to_dict()))

    async def get_thoughts_for_canvas(self, canvas_id: str) -> List[AgentThought]:
        """Get all thoughts for a specific canvas"""
        if canvas_id not in self.thought_cache:
            return []

        return list(self.thought_cache[canvas_id].values())

    async def get_thought_tree(self, canvas_id: str, root_thought_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the thought tree for visualization

        Returns a tree structure with nodes and edges
        """
        if canvas_id not in self.thought_cache:
            return {"nodes": [], "edges": []}

        thoughts = list(self.thought_cache[canvas_id].values())

        # If no root specified, use thoughts without parents as roots
        roots = []
        if root_thought_id:
            if root_thought_id in self.thought_cache.get(canvas_id, {}):
                roots = [self.thought_cache[canvas_id][root_thought_id]]
            else:
                return {"nodes": [], "edges": []}
        else:
            roots = [t for t in thoughts if not t.parent_thought_id]

        # Build node and edge lists
        nodes = []
        edges = []

        # Process all thoughts
        for thought in thoughts:
            # Skip if filtering by root and not in subtree (simple implementation)
            if root_thought_id and thought.thought_id != root_thought_id and not self._is_descendant(canvas_id, root_thought_id, thought.thought_id):
                continue

            # Add node
            nodes.append({
                "id": thought.thought_id,
                "label": thought.content[:50] + "..." if len(thought.content) > 50 else thought.content,
                "role": thought.agent_role,
                "type": thought.thought_type,
                "confidence": thought.confidence,
                "position": thought.visual_position,
                "data": thought.to_dict()
            })

            # Add edge from parent
            if thought.parent_thought_id:
                edges.append({
                    "id": f"{thought.parent_thought_id}_{thought.thought_id}",
                    "source": thought.parent_thought_id,
                    "target": thought.thought_id,
                    "type": "parent"
                })

            # Add edges for references
            for ref_id in thought.references:
                if ref_id in self.thought_cache.get(canvas_id, {}):
                    edges.append({
                        "id": f"{thought.thought_id}_ref_{ref_id}",
                        "source": thought.thought_id,
                        "target": ref_id,
                        "type": "reference"
                    })

        return {
            "nodes": nodes,
            "edges": edges
        }

    def _is_descendant(self, canvas_id: str, ancestor_id: str, descendant_id: str, visited=None) -> bool:
        """Check if a thought is a descendant of another thought"""
        if visited is None:
            visited = set()

        if descendant_id in visited:
            return False

        visited.add(descendant_id)

        # Get thought
        if canvas_id not in self.thought_cache or descendant_id not in self.thought_cache[canvas_id]:
            return False

        thought = self.thought_cache[canvas_id][descendant_id]

        # Check if direct child
        if thought.parent_thought_id == ancestor_id:
            return True

        # Check parent recursively
        if thought.parent_thought_id:
            return self._is_descendant(canvas_id, ancestor_id, thought.parent_thought_id, visited)

        return False

    async def generate_collective_response(self, canvas_id: str, question: str, visualization: bool = True) -> Dict[str, Any]:
        """Generate a collective response from all agents to a question about a canvas"""
        # Initialize team if not already done
        team = await self.initialize_standard_team(canvas_id)

        # Create initial thought from coordinator
        coordinator = team[AgentRole.COORDINATOR]
        initial_thought = await coordinator.generate_thought(
            prompt=f"Question: {question}\nAs the coordinator, formulate an initial approach to answer this question.",
            thought_type=ThoughtType.INITIAL,
            canvas_id=canvas_id
        )

        # Assign analysis tasks to different agents based on question type
        tasks = []

        # Analyst provides data and factual analysis
        tasks.append(team[AgentRole.ANALYST].generate_thought(
            prompt=f"Question: {question}\nAnalyze this question from a data and factual perspective.",
            thought_type=ThoughtType.ANALYTICAL,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id
        ))

        # Designer provides creative perspective
        tasks.append(team[AgentRole.DESIGNER].generate_thought(
            prompt=f"Question: {question}\nConsider this question from a design and visual perspective.",
            thought_type=ThoughtType.CREATIVE,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id
        ))

        # Researcher provides additional context
        tasks.append(team[AgentRole.RESEARCHER].generate_thought(
            prompt=f"Question: {question}\nProvide relevant research context for this question.",
            thought_type=ThoughtType.ANALYTICAL,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id
        ))

        # Wait for all thoughts to be generated
        agent_thoughts = await asyncio.gather(*tasks)

        # Reviewer provides criticism and identifies gaps
        reviewer = team[AgentRole.REVIEWER]
        review_thought = await reviewer.generate_thought(
            prompt=f"Question: {question}\nInitial thoughts: {[t.content for t in agent_thoughts]}\nIdentify gaps or issues in the current analysis.",
            thought_type=ThoughtType.CRITICAL,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id,
            references=[t.thought_id for t in agent_thoughts]
        )

        # Writer summarizes and creates final response
        writer = team[AgentRole.WRITER]
        summary_thought = await writer.generate_thought(
            prompt=f"Question: {question}\nConsider all previous thoughts and create a comprehensive answer.\nInitial approach: {initial_thought.content}\nAnalysis: {[t.content for t in agent_thoughts]}\nReview: {review_thought.content}",
            thought_type=ThoughtType.SUMMARY,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id,
            references=[t.thought_id for t in agent_thoughts] + [review_thought.thought_id]
        )

        # Coordinator makes final decision
        decision_thought = await coordinator.generate_thought(
            prompt=f"Question: {question}\nBased on all analysis, provide the final authoritative answer.\nSummary: {summary_thought.content}",
            thought_type=ThoughtType.DECISION,
            canvas_id=canvas_id,
            parent_thought_id=initial_thought.thought_id,
            references=[summary_thought.thought_id]
        )

        # Create response
        response = {
            "answer": decision_thought.content,
            "thought_id": decision_thought.thought_id
        }

        # Add visualization if requested
        if visualization:
            response["visualization"] = await self.get_thought_tree(canvas_id, initial_thought.thought_id)

        return response
