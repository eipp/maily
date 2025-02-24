from pydantic import BaseModel, Field
from typing import Optional

class ErrorResponse(BaseModel):
    code: str
    message: str

class BaseResponse(BaseModel):
    status: str = Field(..., example="success")
    error: Optional[ErrorResponse] = None