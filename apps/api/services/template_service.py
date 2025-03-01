from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..database.models import EmailTemplate, User
from ..models.template import TemplateCreate, TemplateUpdate
from ..errors.exceptions import TemplateNotFoundError, UnauthorizedError


class TemplateService:
    def __init__(self, db: Session):
        self.db = db

    async def create_template(self, user_id: int, template_data: TemplateCreate) -> EmailTemplate:
        """Create a new email template for a user."""
        template = EmailTemplate(
            user_id=user_id,
            name=template_data.name,
            description=template_data.description,
            content=template_data.content,
            thumbnail=template_data.thumbnail,
            category=template_data.category,
            tags=template_data.tags,
            is_public=template_data.is_public
        )

        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    async def get_template(self, template_id: int, user_id: Optional[int] = None) -> EmailTemplate:
        """Get a template by ID.

        If user_id is provided, it checks if the user has access to the template.
        """
        template = self.db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()

        if not template:
            raise TemplateNotFoundError(f"Template with ID {template_id} not found")

        # Check if user has access to template (either owns it or it's public)
        if user_id and template.user_id != user_id and not template.is_public:
            raise UnauthorizedError("You do not have access to this template")

        return template

    async def update_template(
        self,
        template_id: int,
        user_id: int,
        template_data: TemplateUpdate
    ) -> EmailTemplate:
        """Update an existing template."""
        template = await self.get_template(template_id)

        # Check if user owns the template
        if template.user_id != user_id:
            raise UnauthorizedError("You do not have permission to update this template")

        # Update version number if content is being changed
        if template_data.content is not None:
            template_data.version = template.version + 1

        # Update template fields
        for key, value in template_data.dict(exclude_unset=True).items():
            setattr(template, key, value)

        self.db.commit()
        self.db.refresh(template)
        return template

    async def delete_template(self, template_id: int, user_id: int) -> bool:
        """Delete a template."""
        template = await self.get_template(template_id)

        # Check if user owns the template
        if template.user_id != user_id:
            raise UnauthorizedError("You do not have permission to delete this template")

        self.db.delete(template)
        self.db.commit()
        return True

    async def list_templates(
        self,
        user_id: Optional[int] = None,
        page: int = 1,
        size: int = 20,
        category: Optional[str] = None,
        search: Optional[str] = None,
        include_public: bool = True
    ) -> Dict[str, Any]:
        """List templates with pagination and filtering options."""
        query = self.db.query(EmailTemplate)

        # Filter by user_id and/or public templates
        if user_id:
            if include_public:
                query = query.filter(
                    (EmailTemplate.user_id == user_id) |
                    (EmailTemplate.is_public == True)
                )
            else:
                query = query.filter(EmailTemplate.user_id == user_id)
        elif include_public:
            query = query.filter(EmailTemplate.is_public == True)

        # Apply category filter if provided
        if category:
            query = query.filter(EmailTemplate.category == category)

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                EmailTemplate.name.ilike(search_term) |
                EmailTemplate.description.ilike(search_term)
            )

        # Get total count
        total = query.count()

        # Apply pagination
        query = query.order_by(desc(EmailTemplate.updated_at))
        query = query.offset((page - 1) * size).limit(size)

        templates = query.all()

        return {
            "items": templates,
            "total": total,
            "page": page,
            "size": size
        }

    async def get_featured_templates(
        self,
        limit: int = 10
    ) -> List[EmailTemplate]:
        """Get a list of featured templates."""
        templates = self.db.query(EmailTemplate).filter(
            EmailTemplate.is_featured == True,
            EmailTemplate.is_public == True
        ).order_by(desc(EmailTemplate.updated_at)).limit(limit).all()

        return templates

    async def duplicate_template(
        self,
        template_id: int,
        user_id: int,
        new_name: Optional[str] = None
    ) -> EmailTemplate:
        """Create a duplicate of an existing template."""
        template = await self.get_template(template_id, user_id)

        # Create new name if not provided
        if not new_name:
            new_name = f"{template.name} (Copy)"

        # Create new template
        new_template = EmailTemplate(
            user_id=user_id,
            name=new_name,
            description=template.description,
            content=template.content,
            thumbnail=template.thumbnail,
            category=template.category,
            tags=template.tags,
            is_public=False  # By default, duplicates are private
        )

        self.db.add(new_template)
        self.db.commit()
        self.db.refresh(new_template)
        return new_template
