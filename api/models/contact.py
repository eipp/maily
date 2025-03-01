from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ContactHealthScore(BaseModel):
    """Health score model for contact intelligence."""
    overall: int = Field(0, description="Overall health score (0-100)")
    email_validity: float = Field(0.0, description="Email validity score (0-100)")
    engagement: float = Field(0.0, description="Engagement score (0-100)")
    deliverability: float = Field(0.0, description="Deliverability score (0-100)")
    consent_level: str = Field("unknown", description="Consent level (explicit, implied, unknown)")
    domain_reputation: float = Field(0.0, description="Domain reputation score (0-1)")
    last_evaluated: str = Field(..., description="ISO timestamp of last evaluation")

class Contact(BaseModel):
    """Contact model with enhanced intelligence features."""
    id: str
    name: str
    email: str
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    created_at: str
    updated_at: str
    quality_score: float = 0.0
    tags: List[str] = []

    # Enhanced contact intelligence fields
    health_score: Optional[ContactHealthScore] = None
    verification_status: Optional[Dict[str, bool]] = None
    engagement_metrics: Optional[Dict[str, Any]] = None
    bounce_history: Optional[Dict[str, Any]] = None
    social_profiles: Optional[Dict[str, str]] = None
    custom_fields: Optional[Dict[str, Any]] = {}
    compliance_info: Optional[Dict[str, Any]] = None
    decay_prediction: Optional[Dict[str, Any]] = None
    blockchain_verification: Optional[Dict[str, Any]] = None
