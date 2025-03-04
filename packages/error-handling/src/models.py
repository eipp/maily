"""
Error models for Python services

This module provides standard error models used across Python services.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import traceback
import sys

T = TypeVar('T')

class ErrorResponse(BaseModel):
    """Standard error response model"""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    trace_id: str = Field(..., description="Unique trace ID for error tracking")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class ApiErrorResponse(BaseModel):
    """API error response wrapper"""
    error: ErrorResponse

class ValidationErrorItem(BaseModel):
    """Validation error for a single field"""
    loc: List[str] = Field(..., description="Location of the error (field path)")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    detail: List[ValidationErrorItem]

class ApiResponse(Generic[T], BaseModel):
    """API response model with data or error"""
    data: Optional[T] = None
    error: Optional[ErrorResponse] = None
    success: bool = Field(True, description="Whether the request was successful")

def create_error_response(
    message: str,
    code: str = "INTERNAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    status_code: int = 500
) -> ApiErrorResponse:
    """Create a standardized error response"""
    
    if trace_id is None:
        trace_id = f"err_{uuid.uuid4().hex}"
    
    error = ErrorResponse(
        code=code,
        message=message,
        details=details,
        trace_id=trace_id,
        timestamp=datetime.utcnow()
    )
    
    return ApiErrorResponse(error=error)

def format_exception() -> Dict[str, Any]:
    """Format the current exception into a structured dictionary"""
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    if exc_type is None or exc_value is None or exc_traceback is None:
        return {"error": "No exception information available"}
    
    return {
        "type": exc_type.__name__,
        "message": str(exc_value),
        "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
    }