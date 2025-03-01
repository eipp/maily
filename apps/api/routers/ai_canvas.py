from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from ..services.ai_orchestrator import get_ai_orchestrator, AgentThought, AIOrchestrator
from ..middleware.auth0 import Auth0JWTBearer

router = APIRouter()
auth_handler = Auth0JWTBearer(auto_error=True)

class ThoughtTreeResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class AgentThoughtResponse(BaseModel):
    agent_id: str
    agent_role: str
    thought_id: str
    content: str
    thought_type: str
    canvas_id: str
    timestamp: str
    references: List[str]
    parent_thought_id: Optional[str] = None
    metadata: Dict[str, Any]
    confidence: float
    visual_position: Dict[str, float]

class QuestionRequest(BaseModel):
    question: str
    canvas_id: str
    visualization: bool = True

class QuestionResponse(BaseModel):
    answer: str
    thought_id: str
    visualization: Optional[ThoughtTreeResponse] = None

@router.post("/v1/canvas/ai/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    token_payload: Dict = Depends(auth_handler)
):
    """Generate a multi-agent response to a question about a canvas"""
    try:
        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        orchestrator: AIOrchestrator = await get_ai_orchestrator()

        # Request collective response from agents
        result = await orchestrator.generate_collective_response(
            canvas_id=request.canvas_id,
            question=request.question,
            visualization=request.visualization
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@router.get("/v1/canvas/ai/thoughts/{canvas_id}", response_model=List[AgentThoughtResponse])
async def get_thoughts(
    canvas_id: str,
    token_payload: Dict = Depends(auth_handler)
):
    """Get all thoughts for a specific canvas"""
    try:
        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        orchestrator: AIOrchestrator = await get_ai_orchestrator()

        # Get thoughts for canvas
        thoughts = await orchestrator.get_thoughts_for_canvas(canvas_id)

        # Convert to response format
        return [thought.to_dict() for thought in thoughts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thoughts: {str(e)}")

@router.get("/v1/canvas/ai/thought_tree/{canvas_id}", response_model=ThoughtTreeResponse)
async def get_thought_tree(
    canvas_id: str,
    root_thought_id: Optional[str] = Query(None),
    token_payload: Dict = Depends(auth_handler)
):
    """Get the thought tree for visualization"""
    try:
        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        orchestrator: AIOrchestrator = await get_ai_orchestrator()

        # Get thought tree
        tree = await orchestrator.get_thought_tree(canvas_id, root_thought_id)

        return tree
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thought tree: {str(e)}")

@router.post("/v1/canvas/ai/generate_thought", response_model=AgentThoughtResponse)
async def generate_thought(
    canvas_id: str,
    agent_role: str = Query(..., description="Agent role: coordinator, designer, analyst, writer, researcher, reviewer"),
    prompt: str = Body(..., embed=True),
    parent_thought_id: Optional[str] = Query(None),
    thought_type: str = Query("analytical"),
    token_payload: Dict = Depends(auth_handler)
):
    """Generate a single thought from a specific agent role"""
    try:
        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")

        orchestrator: AIOrchestrator = await get_ai_orchestrator()

        # Find or create agent for this role
        team = await orchestrator.initialize_standard_team(canvas_id)
        agent = team.get(agent_role.lower())

        if not agent:
            raise HTTPException(status_code=400, detail=f"Invalid agent role: {agent_role}")

        # Generate thought
        thought = await agent.generate_thought(
            prompt=prompt,
            thought_type=thought_type,
            canvas_id=canvas_id,
            parent_thought_id=parent_thought_id
        )

        return thought.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating thought: {str(e)}")
