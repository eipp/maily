"""
Prompt Template Manager

This module provides a system for managing and using prompt templates.
Templates can be stored, retrieved, and rendered with variables.
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class PromptTemplate(BaseModel):
    """Model for a prompt template."""
    id: str
    name: str
    description: str
    template: str
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

    @validator('id')
    def validate_id(cls, v):
        if not re.match(r'^[a-z0-9_-]+$', v):
            raise ValueError('ID must contain only lowercase letters, numbers, underscores, and hyphens')
        return v


class TemplateManager:
    """
    Manager for prompt templates.

    This class provides methods for storing, retrieving, and rendering
    prompt templates with variables.
    """

    def __init__(self, templates_dir: str = None):
        """
        Initialize the template manager.

        Args:
            templates_dir: Directory to store templates. If None, uses the default directory.
        """
        self.templates_dir = templates_dir or os.path.join(os.path.dirname(__file__), "templates")
        self.templates: Dict[str, PromptTemplate] = {}
        self._ensure_templates_dir()
        self._load_templates()

    def _ensure_templates_dir(self) -> None:
        """Ensure the templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)

    def _load_templates(self) -> None:
        """Load templates from the templates directory."""
        if not os.path.exists(self.templates_dir):
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(self.templates_dir, filename), "r") as f:
                        template_data = json.load(f)
                        template = PromptTemplate(**template_data)
                        self.templates[template.id] = template
                except Exception as e:
                    logger.error(f"Error loading template {filename}: {str(e)}")

    def save_template(self, template: PromptTemplate) -> bool:
        """
        Save a template to the templates directory.

        Args:
            template: The template to save.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Update timestamps
            if template.id in self.templates:
                template.created_at = self.templates[template.id].created_at
            template.updated_at = datetime.utcnow()

            # Save to file
            with open(os.path.join(self.templates_dir, f"{template.id}.json"), "w") as f:
                f.write(template.json(indent=2))

            # Update in-memory cache
            self.templates[template.id] = template

            return True
        except Exception as e:
            logger.error(f"Error saving template {template.id}: {str(e)}")
            return False

    def get_template(self, template_id: str) -> Optional[PromptTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: The ID of the template to get.

        Returns:
            The template, or None if not found.
        """
        return self.templates.get(template_id)

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: The ID of the template to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if template_id not in self.templates:
                return False

            # Delete file
            file_path = os.path.join(self.templates_dir, f"{template_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)

            # Remove from in-memory cache
            del self.templates[template_id]

            return True
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            return False

    def list_templates(self, tag: Optional[str] = None) -> List[PromptTemplate]:
        """
        List all templates, optionally filtered by tag.

        Args:
            tag: Optional tag to filter by.

        Returns:
            A list of templates.
        """
        if tag:
            return [t for t in self.templates.values() if tag in t.tags]
        return list(self.templates.values())

    def render_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Render a template with variables.

        Args:
            template_id: The ID of the template to render.
            variables: Variables to use in rendering.

        Returns:
            The rendered template.

        Raises:
            ValueError: If the template is not found.
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Simple variable substitution
        rendered = template.template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))

        return rendered

    def create_template(
        self,
        id: str,
        name: str,
        description: str,
        template: str,
        tags: List[str] = [],
        metadata: Dict[str, Any] = {}
    ) -> PromptTemplate:
        """
        Create a new template.

        Args:
            id: The ID of the template.
            name: The name of the template.
            description: The description of the template.
            template: The template text.
            tags: Optional tags for the template.
            metadata: Optional metadata for the template.

        Returns:
            The created template.

        Raises:
            ValueError: If a template with the given ID already exists.
        """
        if id in self.templates:
            raise ValueError(f"Template {id} already exists")

        template = PromptTemplate(
            id=id,
            name=name,
            description=description,
            template=template,
            tags=tags,
            metadata=metadata
        )

        self.save_template(template)
        return template

    def update_template(
        self,
        id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        template: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PromptTemplate:
        """
        Update an existing template.

        Args:
            id: The ID of the template to update.
            name: Optional new name for the template.
            description: Optional new description for the template.
            template: Optional new template text.
            tags: Optional new tags for the template.
            metadata: Optional new metadata for the template.

        Returns:
            The updated template.

        Raises:
            ValueError: If the template is not found.
        """
        existing = self.get_template(id)
        if not existing:
            raise ValueError(f"Template {id} not found")

        # Update fields
        if name is not None:
            existing.name = name
        if description is not None:
            existing.description = description
        if template is not None:
            existing.template = template
        if tags is not None:
            existing.tags = tags
        if metadata is not None:
            existing.metadata = metadata

        # Increment version
        major, minor, patch = existing.version.split(".")
        existing.version = f"{major}.{minor}.{int(patch) + 1}"

        self.save_template(existing)
        return existing


# Create a singleton instance
template_manager = TemplateManager()
