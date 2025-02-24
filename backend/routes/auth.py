from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
import os

API_KEY = os.getenv("API_KEY", "mock-api-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class AuthenticationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

async def get_api_key(api_key: str = Depends(api_key_header)):
    """Validate API key from request header."""
    if not api_key or api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key 