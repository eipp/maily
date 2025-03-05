"""
Standardized User model for use across all Maily services in Python.

This model represents user data and is intended to be used by any service
that needs to interact with user information.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, root_validator


class UserRole(str, Enum):
    """User roles available in the system"""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    ANALYST = "analyst"


class UserStatus(str, Enum):
    """User status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class NotificationSettings(BaseModel):
    """User notification settings"""
    email: bool = True
    in_app: bool = True
    mobile: bool = False


class UserPreferences(BaseModel):
    """User preferences model"""
    theme: str = "system"
    email_frequency: str = "weekly"
    timezone: str = "UTC"
    notification_settings: Optional[NotificationSettings] = None
    default_language: str = "en"

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True


class UserAuth(BaseModel):
    """Authentication related fields for a User"""
    auth_id: Optional[str] = None
    provider: str = "email"
    is_email_verified: bool = False
    password_last_changed: Optional[datetime] = None
    mfa_enabled: bool = False

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True


class User(BaseModel):
    """
    User model representing a Maily user.
    This model is used across all services.
    """
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: Optional[str] = None
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.VIEWER])
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    preferences: Optional[UserPreferences] = None
    metadata: Optional[Dict[str, Any]] = None
    auth: Optional[UserAuth] = None
    organization_id: Optional[UUID] = None

    @root_validator(pre=True)
    def set_full_name(cls, values):
        """Set full_name if not provided"""
        if not values.get("full_name") and values.get("first_name") and values.get("last_name"):
            values["full_name"] = f"{values['first_name']} {values['last_name']}"
        return values

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True
        use_enum_values = True


class UserHelpers:
    """Helper methods for working with User objects"""
    
    @staticmethod
    def get_full_name(user: User) -> str:
        """Get the full name of a user"""
        if user.full_name:
            return user.full_name
        return f"{user.first_name} {user.last_name}"
    
    @staticmethod
    def has_role(user: User, role: Union[UserRole, str]) -> bool:
        """Check if user has a specific role"""
        if isinstance(role, str):
            return role in [r.value if isinstance(r, UserRole) else r for r in user.roles]
        return role in user.roles
    
    @staticmethod
    def is_active(user: User) -> bool:
        """Check if user is active"""
        return user.status == UserStatus.ACTIVE
    
    @staticmethod
    def create_default(email: str, first_name: str, last_name: str) -> User:
        """Create a default user object"""
        now = datetime.utcnow()
        return User(
            id=uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=f"{first_name} {last_name}",
            status=UserStatus.PENDING_VERIFICATION,
            roles=[UserRole.VIEWER],
            created_at=now,
            updated_at=now,
            auth=UserAuth(
                provider="email",
                is_email_verified=False,
                mfa_enabled=False
            )
        )


# Function to convert between TS and Python models
def from_ts_model(ts_data: Dict[str, Any]) -> User:
    """Convert TypeScript model dict to Python model"""
    # Handle field name conversions (camelCase to snake_case)
    field_mappings = {
        "firstName": "first_name",
        "lastName": "last_name",
        "fullName": "full_name",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "lastLogin": "last_login",
        "organizationId": "organization_id"
    }
    
    # Transform nested objects
    if "preferences" in ts_data and ts_data["preferences"]:
        prefs = ts_data["preferences"]
        if "emailFrequency" in prefs:
            prefs["email_frequency"] = prefs.pop("emailFrequency")
        if "notificationSettings" in prefs:
            ns = prefs["notificationSettings"]
            if "inApp" in ns:
                ns["in_app"] = ns.pop("inApp")
            prefs["notification_settings"] = ns
        ts_data["preferences"] = prefs
    
    # Transform auth data
    if "auth" in ts_data and ts_data["auth"]:
        auth = ts_data["auth"]
        if "authId" in auth:
            auth["auth_id"] = auth.pop("authId")
        if "isEmailVerified" in auth:
            auth["is_email_verified"] = auth.pop("isEmailVerified") 
        if "passwordLastChanged" in auth:
            auth["password_last_changed"] = auth.pop("passwordLastChanged")
        if "mfaEnabled" in auth:
            auth["mfa_enabled"] = auth.pop("mfaEnabled")
        ts_data["auth"] = auth
    
    # Apply field mappings
    python_data = {}
    for key, value in ts_data.items():
        python_key = field_mappings.get(key, key)
        python_data[python_key] = value
    
    # Convert date strings to datetime objects
    for date_field in ["created_at", "updated_at", "last_login"]:
        if date_field in python_data and isinstance(python_data[date_field], str):
            python_data[date_field] = datetime.fromisoformat(python_data[date_field].replace("Z", "+00:00"))
    
    # Create the Pydantic model
    return User(**python_data)


def to_ts_model(user: User) -> Dict[str, Any]:
    """Convert Python User model to TypeScript compatible dict"""
    user_dict = user.dict()
    
    # Handle field name conversions (snake_case to camelCase)
    field_mappings = {
        "first_name": "firstName",
        "last_name": "lastName",
        "full_name": "fullName",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "last_login": "lastLogin",
        "organization_id": "organizationId"
    }
    
    # Transform preferences
    if "preferences" in user_dict and user_dict["preferences"]:
        prefs = user_dict["preferences"]
        if "email_frequency" in prefs:
            prefs["emailFrequency"] = prefs.pop("email_frequency")
        if "notification_settings" in prefs:
            ns = prefs["notification_settings"]
            if "in_app" in ns:
                ns["inApp"] = ns.pop("in_app")
            prefs["notificationSettings"] = ns
        user_dict["preferences"] = prefs
    
    # Transform auth data
    if "auth" in user_dict and user_dict["auth"]:
        auth = user_dict["auth"]
        if "auth_id" in auth:
            auth["authId"] = auth.pop("auth_id")
        if "is_email_verified" in auth:
            auth["isEmailVerified"] = auth.pop("is_email_verified")
        if "password_last_changed" in auth:
            auth["passwordLastChanged"] = auth.pop("password_last_changed")
        if "mfa_enabled" in auth:
            auth["mfaEnabled"] = auth.pop("mfa_enabled")
        user_dict["auth"] = auth
    
    # Apply field mappings
    ts_data = {}
    for key, value in user_dict.items():
        ts_key = field_mappings.get(key, key)
        ts_data[ts_key] = value
    
    # Convert datetime objects to ISO strings
    for date_field in ["createdAt", "updatedAt", "lastLogin"]:
        if date_field in ts_data and isinstance(ts_data[date_field], datetime):
            ts_data[date_field] = ts_data[date_field].isoformat()
    
    # Convert UUID objects to strings
    for uuid_field in ["id", "organizationId"]:
        if uuid_field in ts_data and isinstance(ts_data[uuid_field], UUID):
            ts_data[uuid_field] = str(ts_data[uuid_field])
    
    return ts_data