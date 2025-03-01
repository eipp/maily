from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from api.services.auth_service import get_current_user
from api.services.contact_service import contact_service
from api.models.contact import ContactCreate, Contact, ContactListResponse
from api.models.user import User

router = APIRouter()

class ContactDiscoveryRequest(BaseModel):
    target_criteria: Dict[str, Any]
    discovery_depth: Optional[str] = "standard"
    enrichment_level: Optional[str] = "standard"

class LookalikeAudienceRequest(BaseModel):
    seed_contact_ids: List[str]
    expansion_factor: Optional[int] = 3
    similarity_threshold: Optional[float] = 0.7

@router.post("/discover", response_model=ContactListResponse)
async def discover_contacts(
    request: ContactDiscoveryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Discover new contacts based on target criteria.
    """
    contacts = await contact_service.discover_contacts(
        user_id=current_user.id,
        target_criteria=request.target_criteria,
        discovery_depth=request.discovery_depth,
        enrichment_level=request.enrichment_level
    )

    return ContactListResponse(
        contacts=contacts,
        count=len(contacts),
        has_more=False
    )

@router.post("/lookalike")
async def generate_lookalike_audience(
    request: LookalikeAudienceRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generate lookalike contacts based on seed contacts.
    """
    # Get seed contacts from the database
    seed_contacts = await contact_service.get_contacts_by_ids(
        user_id=current_user.id,
        contact_ids=request.seed_contact_ids
    )

    if not seed_contacts:
        raise HTTPException(status_code=404, detail="No seed contacts found")

    # Generate lookalike audience
    result = await contact_service.generate_lookalike_audience(
        user_id=current_user.id,
        seed_contacts=seed_contacts,
        expansion_factor=request.expansion_factor,
        similarity_threshold=request.similarity_threshold
    )

    return result

@router.get("", response_model=ContactListResponse)
async def get_contacts(
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """
    Get contacts for the current user.
    """
    contacts, total = await contact_service.get_contacts(
        user_id=current_user.id,
        search=search,
        limit=limit,
        offset=offset
    )

    return ContactListResponse(
        contacts=contacts,
        count=len(contacts),
        has_more=offset + limit < total
    )
