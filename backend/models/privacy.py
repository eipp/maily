from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

class ConsentStatus(str, Enum):
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"

class RequestStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConsentPreferences(BaseModel):
    user_id: str
    essential: bool = True  # Essential cookies are always required
    functional: bool = False
    analytics: bool = False
    marketing: bool = False
    notification_preferences: Optional[Dict] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "essential": True,
                "functional": True,
                "analytics": False,
                "marketing": False,
                "notification_preferences": {
                    "email_updates": True,
                    "product_news": False
                },
                "last_updated": "2024-03-20T10:00:00Z",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0..."
            }
        }

class DataDeletionRequest(BaseModel):
    id: str
    user_id: str
    status: RequestStatus = RequestStatus.PENDING
    request_date: datetime = Field(default_factory=datetime.utcnow)
    execution_date: datetime  # When the deletion will be executed (after cooling period)
    completed_date: Optional[datetime] = None
    reason: Optional[str] = None
    data_categories: List[str] = Field(default_factory=list)  # Categories of data to be deleted

    class Config:
        json_schema_extra = {
            "example": {
                "id": "del_123",
                "user_id": "user123",
                "status": "pending",
                "request_date": "2024-03-20T10:00:00Z",
                "execution_date": "2024-04-19T10:00:00Z",
                "data_categories": ["personal_info", "analytics", "campaigns"]
            }
        }

class DataExportRequest(BaseModel):
    id: str
    user_id: str
    status: RequestStatus = RequestStatus.PENDING
    request_date: datetime = Field(default_factory=datetime.utcnow)
    completed_date: Optional[datetime] = None
    download_url: Optional[str] = None
    expiry_date: Optional[datetime] = None  # When the download URL expires
    format: str = "json"  # Export format (json, csv, etc.)
    data_categories: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "exp_123",
                "user_id": "user123",
                "status": "completed",
                "request_date": "2024-03-20T10:00:00Z",
                "completed_date": "2024-03-20T10:05:00Z",
                "download_url": "https://example.com/exports/exp_123.zip",
                "expiry_date": "2024-03-27T10:05:00Z",
                "format": "json",
                "data_categories": ["personal_info", "campaigns", "analytics"]
            }
        }

class ConsentLog(BaseModel):
    id: str
    user_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str  # e.g., "update", "revoke", "grant"
    preferences_before: Optional[Dict] = None
    preferences_after: Dict
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "log_123",
                "user_id": "user123",
                "timestamp": "2024-03-20T10:00:00Z",
                "action": "update",
                "preferences_before": {
                    "essential": True,
                    "functional": False,
                    "analytics": False,
                    "marketing": False
                },
                "preferences_after": {
                    "essential": True,
                    "functional": True,
                    "analytics": True,
                    "marketing": False
                },
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0..."
            }
        } 