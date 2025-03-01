"""
Templates Router

This module provides endpoints for managing email templates and prompt templates.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from ..database.dependencies import get_db
from ..models.template import TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse
from ..services.template_service import TemplateService
from ..auth.dependencies import get_current_user
from ..database.models import User
from ..errors.exceptions import TemplateNotFoundError, UnauthorizedError
from ..monitoring.metrics import MetricsManager
from ..ai.prompts.template_manager import template_manager, PromptTemplate

router = APIRouter(prefix="/templates", tags=["templates"])
metrics = MetricsManager()


# Prompt Template Models
class PromptTemplateCreate(BaseModel):
    """Request model for creating a prompt template."""
    id: str
    name: str
    description: str
    template: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class PromptTemplateUpdate(BaseModel):
    """Request model for updating a prompt template."""
    name: Optional[str] = None
    description: Optional[str] = None
    template: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class PromptTemplateRender(BaseModel):
    """Request model for rendering a prompt template."""
    template_id: str
    variables: Dict[str, Any]


class PromptTemplateResponse(BaseModel):
    """Response model for a prompt template."""
    id: str
    name: str
    description: str
    template: str
    version: str
    created_at: str
    updated_at: str
    tags: List[str]
    metadata: Dict[str, Any]


# Prompt Template Endpoints
@router.get("/prompt-templates", response_model=List[PromptTemplateResponse], tags=["Prompt Templates"])
async def list_prompt_templates(
    tag: Optional[str] = Query(None, description="Filter templates by tag")
):
    """
    List all prompt templates, optionally filtered by tag.

    Args:
        tag: Optional tag to filter by.

    Returns:
        A list of prompt templates.
    """
    templates = template_manager.list_templates(tag)
    return [
        PromptTemplateResponse(
            id=t.id,
            name=t.name,
            description=t.description,
            template=t.template,
            version=t.version,
            created_at=t.created_at.isoformat(),
            updated_at=t.updated_at.isoformat(),
            tags=t.tags,
            metadata=t.metadata
        )
        for t in templates
    ]


@router.get("/prompt-templates/{template_id}", response_model=PromptTemplateResponse, tags=["Prompt Templates"])
async def get_prompt_template(
    template_id: str = Path(..., description="The ID of the template to get")
):
    """
    Get a prompt template by ID.

    Args:
        template_id: The ID of the template to get.

    Returns:
        The prompt template.

    Raises:
        HTTPException: If the template is not found.
    """
    template = template_manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    return PromptTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        template=template.template,
        version=template.version,
        created_at=template.created_at.isoformat(),
        updated_at=template.updated_at.isoformat(),
        tags=template.tags,
        metadata=template.metadata
    )


@router.post("/prompt-templates", response_model=PromptTemplateResponse, tags=["Prompt Templates"])
async def create_prompt_template(
    template: PromptTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new prompt template.

    Args:
        template: The template to create.
        current_user: The current authenticated user.

    Returns:
        The created template.

    Raises:
        HTTPException: If a template with the given ID already exists.
    """
    try:
        created = template_manager.create_template(
            id=template.id,
            name=template.name,
            description=template.description,
            template=template.template,
            tags=template.tags,
            metadata=template.metadata
        )

        return PromptTemplateResponse(
            id=created.id,
            name=created.name,
            description=created.description,
            template=created.template,
            version=created.version,
            created_at=created.created_at.isoformat(),
            updated_at=created.updated_at.isoformat(),
            tags=created.tags,
            metadata=created.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/prompt-templates/{template_id}", response_model=PromptTemplateResponse, tags=["Prompt Templates"])
async def update_prompt_template(
    template_id: str,
    template: PromptTemplateUpdate,
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing prompt template.

    Args:
        template_id: The ID of the template to update.
        template: The template updates.
        current_user: The current authenticated user.

    Returns:
        The updated template.

    Raises:
        HTTPException: If the template is not found.
    """
    try:
        updated = template_manager.update_template(
            id=template_id,
            name=template.name,
            description=template.description,
            template=template.template,
            tags=template.tags,
            metadata=template.metadata
        )

        return PromptTemplateResponse(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            template=updated.template,
            version=updated.version,
            created_at=updated.created_at.isoformat(),
            updated_at=updated.updated_at.isoformat(),
            tags=updated.tags,
            metadata=updated.metadata
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/prompt-templates/{template_id}", tags=["Prompt Templates"])
async def delete_prompt_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a prompt template.

    Args:
        template_id: The ID of the template to delete.
        current_user: The current authenticated user.

    Returns:
        A success message.

    Raises:
        HTTPException: If the template is not found.
    """
    success = template_manager.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template {template_id} not found")

    return {"status": "success", "message": f"Template {template_id} deleted"}


@router.post("/prompt-templates/render", tags=["Prompt Templates"])
async def render_prompt_template(
    request: PromptTemplateRender
):
    """
    Render a prompt template with variables.

    Args:
        request: The render request.

    Returns:
        The rendered template.

    Raises:
        HTTPException: If the template is not found.
    """
    try:
        rendered = template_manager.render_template(
            template_id=request.template_id,
            variables=request.variables
        )

        return {"rendered": rendered}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new email template."""
    template_service = TemplateService(db)
    template = await template_service.create_template(current_user.id, template_data)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a template by ID."""
    try:
        template_service = TemplateService(db)
        template = await template_service.get_template(
            template_id=template_id,
            user_id=current_user.id if current_user else None
        )
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing template."""
    try:
        template_service = TemplateService(db)
        template = await template_service.update_template(
            template_id=template_id,
            user_id=current_user.id,
            template_data=template_data
        )
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a template."""
    try:
        template_service = TemplateService(db)
        await template_service.delete_template(
            template_id=template_id,
            user_id=current_user.id
        )
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    include_public: bool = True,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List templates with pagination and filtering options."""
    template_service = TemplateService(db)
    templates = await template_service.list_templates(
        user_id=current_user.id if current_user else None,
        page=page,
        size=size,
        category=category,
        search=search,
        include_public=include_public
    )
    return templates


@router.get("/featured", response_model=List[TemplateResponse])
async def get_featured_templates(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get a list of featured templates."""
    template_service = TemplateService(db)
    templates = await template_service.get_featured_templates(limit=limit)
    return templates


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
async def duplicate_template(
    template_id: int,
    new_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a duplicate of an existing template."""
    try:
        template_service = TemplateService(db)
        template = await template_service.duplicate_template(
            template_id=template_id,
            user_id=current_user.id,
            new_name=new_name
        )
        return template
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnauthorizedError as e:
        raise HTTPException(status_code=403, detail=str(e))
