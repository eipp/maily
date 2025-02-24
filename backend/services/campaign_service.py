import json
import time
from typing import Dict, Any
from loguru import logger
from .database import get_db_connection
from ..models import ModelAdapter
from .agent_service import create_group_chat

def process_campaign_task(task: str, model_adapter: ModelAdapter, user_id: int) -> Dict[str, Any]:
    """Process a campaign task using the provided model adapter."""
    try:
        # Create a group chat for collaborative campaign generation
        group_chat = create_group_chat(user_id, task)
        
        # Generate campaign content using the group chat
        result = model_adapter.generate(task)
        
        metadata = {
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "task_type": "campaign_generation",
            "model_used": model_adapter.__class__.__name__
        }
        
        return {
            "status": "success",
            "result": result,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Campaign task processing failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "metadata": {
                "error_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error_type": e.__class__.__name__
            }
        }

def save_campaign_result(campaign_id: int, result: Dict[str, Any]) -> None:
    """Save campaign results to the database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if result["status"] == "success":
            cur.execute(
                """
                UPDATE campaigns
                SET result = %s, status = %s, metadata = %s
                WHERE id = %s
                """,
                (json.dumps(result["result"]), "completed", json.dumps(result["metadata"]), campaign_id)
            )
        else:
            cur.execute(
                """
                UPDATE campaigns
                SET status = %s, metadata = %s
                WHERE id = %s
                """,
                ("failed", json.dumps(result["metadata"]), campaign_id)
            )
            
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save campaign result: {e}")
        raise 