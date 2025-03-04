"""
Streaming Router for AI Mesh Network

This module provides streaming endpoints for the AI Mesh Network, allowing clients
to receive real-time, incremental responses from agent tasks through SSE (Server-Sent Events)
and streaming response patterns.

Key features:
1. Server-Sent Events (SSE) for real-time task progress and results
2. Streaming response endpoints for task submissions
3. Token-by-token streaming for agent responses
4. Efficient memory and resource usage through generator-based streaming
5. Support for cancellation and backpressure
"""

import json
import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, Request, Response, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ..services.agent_coordinator import get_agent_coordinator, AgentCoordinator
from ..utils.redis_client import get_redis_client
from ..utils.llm_client import get_llm_client, LLMClient

logger = logging.getLogger("ai_service.routers.streaming_router")

router = APIRouter()

# Task submission queue for streaming tasks
streaming_tasks = {}  # task_id -> TaskStreamInfo

class TaskStreamInfo:
    """Class to track streaming task information"""
    def __init__(self, task_id: str, network_id: str, request_id: str):
        self.task_id = task_id
        self.network_id = network_id
        self.request_id = request_id
        self.status = "pending"
        self.result_queue = asyncio.Queue()
        self.last_update = time.time()
        self.is_complete = False
        self.error = None
        
    async def add_update(self, update_type: str, data: Dict[str, Any]):
        """Add an update to the result queue"""
        await self.result_queue.put({
            "type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.last_update = time.time()
        
    async def complete(self, result: Dict[str, Any] = None):
        """Mark the task as complete"""
        self.is_complete = True
        self.status = "completed"
        if result:
            await self.add_update("result", result)
        await self.add_update("complete", {"status": "completed"})
        
    async def fail(self, error: str):
        """Mark the task as failed"""
        self.is_complete = True
        self.status = "failed"
        self.error = error
        await self.add_update("error", {"error": error})
        await self.add_update("complete", {"status": "failed"})

async def task_result_processor(task_stream: TaskStreamInfo, coordinator: AgentCoordinator):
    """Background task to process a task and stream the results"""
    try:
        # Start task processing
        await task_stream.add_update("started", {
            "task_id": task_stream.task_id,
            "network_id": task_stream.network_id
        })
        
        # Process the task and handle the result streaming
        result = await coordinator.process_task(
            network_id=task_stream.network_id,
            task_id=task_stream.task_id
        )
        
        # Check if the task was processed successfully
        if result.get("status") == "completed":
            # Stream back the final result
            await task_stream.complete(result.get("result"))
        else:
            # Task processing failed
            error_message = result.get("error", "Unknown error")
            await task_stream.fail(error_message)
            
    except Exception as e:
        logger.error(f"Error processing streaming task {task_stream.task_id}: {e}")
        await task_stream.fail(str(e))
    finally:
        # Cleanup after 5 minutes
        asyncio.create_task(cleanup_task_stream(task_stream.task_id, delay=300))

async def cleanup_task_stream(task_id: str, delay: int = 300):
    """Clean up a task stream after a delay"""
    try:
        await asyncio.sleep(delay)
        if task_id in streaming_tasks:
            del streaming_tasks[task_id]
            logger.debug(f"Cleaned up task stream for task {task_id}")
    except Exception as e:
        logger.error(f"Error cleaning up task stream for task {task_id}: {e}")

async def generate_sse_events(task_stream: TaskStreamInfo, request: Request) -> AsyncGenerator[Dict[str, Any], None]:
    """Generate SSE events for a task stream"""
    while not task_stream.is_complete:
        # Check if client is disconnected
        if await request.is_disconnected():
            logger.info(f"Client disconnected from SSE stream for task {task_stream.task_id}")
            break
            
        # Try to get an update from the queue
        try:
            # Use a timeout to periodically check for client disconnection
            update = await asyncio.wait_for(task_stream.result_queue.get(), timeout=1.0)
            yield update
        except asyncio.TimeoutError:
            # Send keep-alive ping every 15 seconds
            if time.time() - task_stream.last_update > 15:
                yield {
                    "type": "ping",
                    "data": {"timestamp": datetime.utcnow().isoformat()},
                    "timestamp": datetime.utcnow().isoformat()
                }
                task_stream.last_update = time.time()
        except Exception as e:
            logger.error(f"Error generating SSE event for task {task_stream.task_id}: {e}")
            yield {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
            break
    
    # If the queue still has items, drain them
    while not task_stream.result_queue.empty():
        try:
            update = task_stream.result_queue.get_nowait()
            yield update
        except:
            break
            
    # Final event to close the stream
    yield {
        "type": "close",
        "data": {"status": task_stream.status},
        "timestamp": datetime.utcnow().isoformat()
    }

async def generate_json_stream(task_stream: TaskStreamInfo, request: Request) -> AsyncGenerator[bytes, None]:
    """Generate a JSON stream for a task"""
    # Send the opening of a JSON array
    yield b'[\n'
    first_item = True
    
    while not task_stream.is_complete:
        # Check if client is disconnected
        if await request.is_disconnected():
            logger.info(f"Client disconnected from JSON stream for task {task_stream.task_id}")
            break
            
        # Try to get an update from the queue
        try:
            # Use a timeout to periodically check for client disconnection
            update = await asyncio.wait_for(task_stream.result_queue.get(), timeout=1.0)
            
            # Add a comma before the item if it's not the first one
            prefix = '' if first_item else ',\n'
            first_item = False
            
            # Convert the update to JSON and yield
            yield f"{prefix}{json.dumps(update)}".encode('utf-8')
        except asyncio.TimeoutError:
            # No update within timeout, just continue
            continue
        except Exception as e:
            logger.error(f"Error generating JSON stream for task {task_stream.task_id}: {e}")
            # If there was an error, add an error event (with proper JSON formatting)
            prefix = '' if first_item else ',\n'
            first_item = False
            error_event = {
                "type": "error",
                "data": {"error": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
            yield f"{prefix}{json.dumps(error_event)}".encode('utf-8')
            break
    
    # If the queue still has items, drain them
    while not task_stream.result_queue.empty():
        try:
            update = task_stream.result_queue.get_nowait()
            prefix = '' if first_item else ',\n'
            first_item = False
            yield f"{prefix}{json.dumps(update)}".encode('utf-8')
        except:
            break
    
    # Add a final closing event
    if not first_item:
        yield b',\n'
    
    final_event = {
        "type": "close",
        "data": {"status": task_stream.status},
        "timestamp": datetime.utcnow().isoformat()
    }
    yield f"{json.dumps(final_event)}\n]".encode('utf-8')

@router.post("/mesh/networks/{network_id}/tasks/stream", tags=["AI Mesh Network - Streaming"])
async def submit_streaming_task(
    request: Request,
    network_id: str,
    task_data: Dict[str, Any],
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """
    Submit a task to a network and receive streaming updates
    
    This endpoint allows clients to submit a task to the AI Mesh Network
    and receive real-time streaming updates on the task's progress and results.
    
    Args:
        network_id: ID of the network to submit task to
        task_data: Task submission data
        
    Returns:
        StreamingResponse with JSON stream of task updates
    """
    try:
        # Generate a request ID for tracking
        request_id = f"req_{time.time()}_{hash(request)}"
        
        # Extract task data with validation
        if "task" not in task_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task description is required"
            )
            
        task = task_data["task"]
        context = task_data.get("context", {})
        priority = min(max(task_data.get("priority", 1), 1), 10)  # Ensure priority is between 1 and 10
        
        # Submit the task to the network
        submission_result = await coordinator.submit_task(
            network_id=network_id,
            task=task,
            context=context,
            priority=priority
        )
        
        # Get the task ID from the submission result
        task_id = submission_result["task_id"]
        
        # Create a TaskStreamInfo object for this task
        task_stream = TaskStreamInfo(
            task_id=task_id,
            network_id=network_id,
            request_id=request_id
        )
        
        # Store the task stream object
        streaming_tasks[task_id] = task_stream
        
        # Start the task processor in the background
        asyncio.create_task(task_result_processor(task_stream, coordinator))
        
        # Return a streaming response
        return StreamingResponse(
            generate_json_stream(task_stream, request),
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting streaming task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting streaming task: {str(e)}"
        )

@router.get("/mesh/tasks/{task_id}/stream", tags=["AI Mesh Network - Streaming"])
async def get_task_stream(
    request: Request,
    task_id: str,
    format: str = "sse",  # Options: sse, json
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """
    Get streaming updates for an existing task
    
    This endpoint allows clients to connect to a stream of updates for an existing task.
    
    Args:
        task_id: ID of the task to stream
        format: Format of the stream (sse or json)
        
    Returns:
        StreamingResponse with task updates in the requested format
    """
    try:
        # Check if task exists
        task = await coordinator.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        network_id = task["network_id"]
        
        # Check if there's already a streaming task object
        if task_id in streaming_tasks:
            task_stream = streaming_tasks[task_id]
        else:
            # Create a new TaskStreamInfo object for this task
            request_id = f"req_{time.time()}_{hash(request)}"
            task_stream = TaskStreamInfo(
                task_id=task_id,
                network_id=network_id,
                request_id=request_id
            )
            streaming_tasks[task_id] = task_stream
            
            # If task is already in progress or completed, handle accordingly
            if task["status"] in ["completed", "failed"]:
                if task["status"] == "completed":
                    # Task is already complete, immediately provide the result
                    await task_stream.complete(task.get("result"))
                else:
                    # Task already failed
                    await task_stream.fail(task.get("error", "Task failed"))
            else:
                # Task is still in progress, start the processor
                asyncio.create_task(task_result_processor(task_stream, coordinator))
        
        # Return the appropriate streaming response based on the requested format
        if format.lower() == "sse":
            return EventSourceResponse(
                generate_sse_events(task_stream, request),
                media_type="text/event-stream"
            )
        else:  # Default to JSON
            return StreamingResponse(
                generate_json_stream(task_stream, request),
                media_type="application/json"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming task updates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming task updates: {str(e)}"
        )

@router.post("/mesh/generate/stream", tags=["AI Mesh Network - Streaming"])
async def streaming_generation(
    request: Request,
    generation_request: Dict[str, Any],
    coordinator: AgentCoordinator = Depends(get_agent_coordinator),
    llm_client: LLMClient = Depends(get_llm_client)
):
    """
    Generate streaming text responses directly from the LLM
    
    This endpoint provides direct access to LLM streaming capabilities,
    allowing token-by-token streaming of generation results.
    
    Args:
        generation_request: Dictionary with generation parameters
            - prompt: The prompt to generate from
            - model: (Optional) Model to use (defaults to coordinator default)
            - temperature: (Optional) Temperature for generation
            - max_tokens: (Optional) Maximum tokens to generate
            
    Returns:
        StreamingResponse with generated tokens
    """
    try:
        # Extract and validate request parameters
        if "prompt" not in generation_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prompt is required"
            )
            
        prompt = generation_request["prompt"]
        model = generation_request.get("model", "claude-3-7-sonnet")  # Default model
        temperature = min(max(generation_request.get("temperature", 0.7), 0), 1)  # 0-1 range
        max_tokens = min(generation_request.get("max_tokens", 4000), 10000)  # Cap at 10k tokens
        
        # Function to stream the generated text
        async def generate_text_stream():
            try:
                # Start streaming with JSON opening
                yield b'{\n'
                yield b'  "status": "streaming",\n'
                yield b'  "tokens": ['
                
                # Stream the content
                first_token = True
                async for chunk in llm_client.generate_text_stream(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    # Format the token as JSON
                    token_data = json.dumps(chunk)
                    prefix = '' if first_token else ','
                    first_token = False
                    
                    # Yield the token
                    yield f"{prefix}{token_data}".encode('utf-8')
                    
                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info("Client disconnected from text generation stream")
                        break
                
                # Close the JSON structure
                yield b'],\n'
                yield b'  "complete": true\n'
                yield b'}'
                
            except Exception as e:
                logger.error(f"Error in text generation stream: {e}")
                # Send error response in valid JSON
                yield b'{\n'
                yield b'  "status": "error",\n'
                yield f'  "error": "{str(e)}",\n'.encode('utf-8')
                yield b'  "complete": true\n'
                yield b'}'
        
        # Return the streaming response
        return StreamingResponse(
            generate_text_stream(),
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in streaming generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in streaming generation: {str(e)}"
        )

# For SSE endpoint with better client support
@router.get("/mesh/tasks/{task_id}/events", tags=["AI Mesh Network - Streaming"])
async def get_task_events(
    request: Request,
    task_id: str,
    coordinator: AgentCoordinator = Depends(get_agent_coordinator)
):
    """
    Get SSE events for an existing task with improved client compatibility
    
    This endpoint provides SSE events for task updates with specific formatting
    that improves compatibility with various SSE client implementations.
    
    Args:
        task_id: ID of the task to stream
        
    Returns:
        EventSourceResponse with task updates
    """
    try:
        # Check if task exists
        task = await coordinator.get_task(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
            
        network_id = task["network_id"]
        
        # Check if there's already a streaming task object
        if task_id in streaming_tasks:
            task_stream = streaming_tasks[task_id]
        else:
            # Create a new TaskStreamInfo object for this task
            request_id = f"req_{time.time()}_{hash(request)}"
            task_stream = TaskStreamInfo(
                task_id=task_id,
                network_id=network_id,
                request_id=request_id
            )
            streaming_tasks[task_id] = task_stream
            
            # If task is already in progress or completed, handle accordingly
            if task["status"] in ["completed", "failed"]:
                if task["status"] == "completed":
                    # Task is already complete, immediately provide the result
                    await task_stream.complete(task.get("result"))
                else:
                    # Task already failed
                    await task_stream.fail(task.get("error", "Task failed"))
            else:
                # Task is still in progress, start the processor
                asyncio.create_task(task_result_processor(task_stream, coordinator))
        
        # Function to generate SSE events with enhanced formatting
        async def generate_enhanced_sse_events():
            async for event in generate_sse_events(task_stream, request):
                event_type = event["type"]
                event_data = json.dumps(event)
                
                # Format as SSE event
                yield f"event: {event_type}\n"
                yield f"data: {event_data}\n\n"
                
                # For keep-alive
                if event_type == "ping":
                    yield ": ping\n\n"
        
        # Return the SSE response
        return EventSourceResponse(
            generate_enhanced_sse_events(),
            media_type="text/event-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming task events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error streaming task events: {str(e)}"
        )

@router.on_event("startup")
async def startup_streaming_router():
    """Initialize the streaming router on startup"""
    logger.info("Initializing AI Mesh Network Streaming Router")
    # Ensure Redis connection is ready
    redis = await get_redis_client()
    # Ensure LLM client is ready
    llm_client = await get_llm_client()
    
    logger.info("AI Mesh Network Streaming Router initialized")

@router.on_event("shutdown")
async def shutdown_streaming_router():
    """Cleanup the streaming router on shutdown"""
    logger.info("Shutting down AI Mesh Network Streaming Router")
    # Clean up any active streams
    for task_id, task_stream in list(streaming_tasks.items()):
        if not task_stream.is_complete:
            await task_stream.fail("Server shutting down")
    
    logger.info("AI Mesh Network Streaming Router shutdown complete")