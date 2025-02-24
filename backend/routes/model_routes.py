from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger
from ..models import MODEL_REGISTRY
from ..services import get_db_connection, cipher_suite
from .schemas import BaseResponse

router = APIRouter()

class ConfigRequest(BaseModel):
    model_name: str
    api_key: str

@router.post("/configure_model", tags=["Models"], summary="Configure AI model")
async def configure_model(config: ConfigRequest):
    try:
        if config.model_name not in MODEL_REGISTRY:
            raise HTTPException(status_code=400, detail=f"Model {config.model_name} not supported")
        
        # Encrypt API key
        encrypted_key = cipher_suite.encrypt(config.api_key.encode()).decode()
        
        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO user_configs (user_id, model_name, api_key)
            VALUES (1, %s, %s)  # TODO: Get user_id from auth
            ON CONFLICT (user_id) DO UPDATE 
            SET model_name = EXCLUDED.model_name, api_key = EXCLUDED.api_key
        """, (config.model_name, encrypted_key))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return BaseResponse(status="success")
    except Exception as e:
        logger.error(f"Failed to configure model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 