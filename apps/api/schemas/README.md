# Maily API Schemas

This directory contains Pydantic schema models that define the data structures for the Maily API.

## Schema Organization

Schemas are organized by domain entity:

```
schemas/
├── auth/                  # Authentication-related schemas
├── campaign/              # Campaign schemas
├── contact/               # Contact schemas
├── email/                 # Email schemas
├── template/              # Template schemas
├── analytics/             # Analytics schemas
├── integration/           # Integration schemas
└── base.py                # Base schema classes
```

## Schema Responsibilities

Schemas are responsible for:

1. Defining the structure of request and response data
2. Validating input data
3. Providing serialization and deserialization
4. Documenting API data structures
5. Enforcing field-level constraints

## Schema Types

For each entity, we typically define several schema types:

1. **Base**: Common fields shared by all schemas for the entity
2. **Create**: Fields required when creating a new entity
3. **Update**: Fields that can be updated (usually all optional)
4. **Response**: Fields returned in API responses
5. **DB**: Fields that match the database model (internal use)

## Schema Structure

Each schema should:

1. Extend the appropriate Pydantic model
2. Define fields with appropriate types and constraints
3. Include field descriptions for API documentation
4. Define validation rules where needed
5. Use nested schemas for complex structures

Example:

```python
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class ContactBase(BaseModel):
    """Base schema for contact data."""
    email: EmailStr = Field(..., description="Contact email address")
    first_name: Optional[str] = Field(None, description="Contact first name")
    last_name: Optional[str] = Field(None, description="Contact last name")


class ContactCreate(ContactBase):
    """Schema for creating a new contact."""
    list_id: int = Field(..., description="ID of the list this contact belongs to")


class ContactUpdate(BaseModel):
    """Schema for updating an existing contact."""
    email: Optional[EmailStr] = Field(None, description="Contact email address")
    first_name: Optional[str] = Field(None, description="Contact first name")
    last_name: Optional[str] = Field(None, description="Contact last name")
    is_active: Optional[bool] = Field(None, description="Whether the contact is active")


class ContactResponse(ContactBase):
    """Schema for contact in API responses."""
    id: int = Field(..., description="Contact ID")
    list_id: int = Field(..., description="ID of the list this contact belongs to")
    is_active: bool = Field(..., description="Whether the contact is active")
    created_at: datetime = Field(..., description="When the contact was created")
    updated_at: Optional[datetime] = Field(None, description="When the contact was last updated")

    class Config:
        orm_mode = True
```

## Config Options

Common Pydantic config options used in our schemas:

```python
class Config:
    # Allow conversion from ORM objects
    orm_mode = True

    # Validate field assignments
    validate_assignment = True

    # Use enum values instead of names
    use_enum_values = True

    # Allow population by field name
    allow_population_by_field_name = True

    # Extra fields handling
    extra = "forbid"  # Forbid extra fields
```

## Validation

Schemas should include appropriate validation:

1. Use Pydantic validators for complex validation
2. Use Field constraints for simple validation
3. Define custom validators for business rules

Example:

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Campaign name")
    subject: str = Field(..., min_length=1, max_length=150, description="Email subject line")
    scheduled_at: Optional[datetime] = Field(None, description="When to send the campaign")

    @validator("scheduled_at")
    def scheduled_at_must_be_future(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("scheduled_at must be in the future")
        return v
```

## Relationships

For related entities, use nested schemas:

```python
from typing import List
from pydantic import BaseModel

from apps.api.schemas.contact import ContactResponse


class ListResponse(BaseModel):
    id: int
    name: str
    contacts: List[ContactResponse] = []

    class Config:
        orm_mode = True
```

## Testing

All schemas should have tests that:

1. Test validation rules
2. Test serialization and deserialization
3. Test conversion from ORM objects
4. Test error cases

## Best Practices

1. **Consistent Naming**: Use consistent naming conventions for all schemas.
2. **Documentation**: Include field descriptions for all fields.
3. **Validation**: Use appropriate validation for all fields.
4. **Separation**: Keep request and response schemas separate.
5. **Reuse**: Use inheritance to reuse common fields.
6. **Simplicity**: Keep schemas focused on their specific use case.
