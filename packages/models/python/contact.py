"""
Standardized Contact model for use across all Maily services in Python.

This model represents contact data and is intended to be used by any service
that needs to interact with contact information.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, AnyUrl, validator


class ContactStatus(str, Enum):
    """Contact status states"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"


class AddressType(str, Enum):
    """Address types"""
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class PhoneType(str, Enum):
    """Phone types"""
    MOBILE = "mobile"
    HOME = "home"
    WORK = "work"
    OTHER = "other"


class CustomFieldType(str, Enum):
    """Custom field types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"


class Address(BaseModel):
    """Address model"""
    street1: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    type: AddressType = AddressType.HOME

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True


class Phone(BaseModel):
    """Phone model"""
    number: str
    type: PhoneType = PhoneType.MOBILE
    primary: bool = False

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True


class CustomField(BaseModel):
    """Custom field model"""
    key: str
    value: Optional[Union[str, int, float, bool]] = None
    type: CustomFieldType = CustomFieldType.STRING

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True


class Consent(BaseModel):
    """Consent model"""
    marketing: bool = False
    transactional: bool = True
    third_party: bool = False
    timestamp: datetime
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True


class Activity(BaseModel):
    """Activity model"""
    type: str  # email_open, email_click, etc.
    timestamp: datetime
    campaign_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True


class Contact(BaseModel):
    """
    Contact model representing a contact in Maily system.
    This model is used across all services.
    """
    id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    status: ContactStatus = ContactStatus.ACTIVE
    source: Optional[str] = None  # form, import, api, etc.
    tags: List[str] = Field(default_factory=list)
    list_ids: List[UUID] = Field(default_factory=list)
    addresses: List[Address] = Field(default_factory=list)
    phones: List[Phone] = Field(default_factory=list)
    custom_fields: List[CustomField] = Field(default_factory=list)
    consent: Optional[Consent] = None
    activity: List[Activity] = Field(default_factory=list)
    last_activity: Optional[datetime] = None
    profile_image: Optional[AnyUrl] = None
    created_at: datetime
    updated_at: datetime
    organization_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator('full_name', pre=True, always=True)
    def set_full_name(cls, v, values):
        """Set full_name if not provided"""
        if not v and 'first_name' in values and 'last_name' in values:
            if values['first_name'] and values['last_name']:
                return f"{values['first_name']} {values['last_name']}"
        return v

    class Config:
        """Pydantic model configuration"""
        allow_population_by_field_name = True
        use_enum_values = True


class ContactHelpers:
    """Helper methods for working with Contact objects"""
    
    @staticmethod
    def get_full_name(contact: Contact) -> str:
        """Get the full name of a contact"""
        if contact.full_name:
            return contact.full_name
        
        if contact.first_name and contact.last_name:
            return f"{contact.first_name} {contact.last_name}"
        
        if contact.first_name:
            return contact.first_name
        
        if contact.last_name:
            return contact.last_name
        
        return ""
    
    @staticmethod
    def has_tag(contact: Contact, tag: str) -> bool:
        """Check if contact has a specific tag"""
        return tag in contact.tags
    
    @staticmethod
    def is_active(contact: Contact) -> bool:
        """Check if contact is active"""
        return contact.status == ContactStatus.ACTIVE
    
    @staticmethod
    def is_subscribed(contact: Contact) -> bool:
        """Check if contact is subscribed (active and has marketing consent)"""
        return (
            contact.status == ContactStatus.ACTIVE and
            contact.consent is not None and
            contact.consent.marketing is True
        )
    
    @staticmethod
    def get_custom_field(contact: Contact, key: str) -> Any:
        """Get a custom field value"""
        for field in contact.custom_fields:
            if field.key == key:
                return field.value
        return None
    
    @staticmethod
    def create_default(email: str, first_name: Optional[str] = None, last_name: Optional[str] = None) -> Contact:
        """Create a default contact object"""
        now = datetime.utcnow()
        full_name = None
        if first_name and last_name:
            full_name = f"{first_name} {last_name}"
            
        return Contact(
            id=uuid4(),
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            status=ContactStatus.ACTIVE,
            tags=[],
            list_ids=[],
            addresses=[],
            phones=[],
            custom_fields=[],
            activity=[],
            created_at=now,
            updated_at=now,
            consent=Consent(
                marketing=False,
                transactional=True,
                third_party=False,
                timestamp=now
            )
        )


# Functions to convert between TS and Python models
def from_ts_model(ts_data: Dict[str, Any]) -> Contact:
    """Convert TypeScript model dict to Python model"""
    # Handle field name conversions (camelCase to snake_case)
    field_mappings = {
        "firstName": "first_name",
        "lastName": "last_name",
        "fullName": "full_name",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "lastActivity": "last_activity",
        "profileImage": "profile_image",
        "organizationId": "organization_id",
        "listIds": "list_ids",
        "customFields": "custom_fields",
        "ipAddress": "ip_address",
        "userAgent": "user_agent",
        "campaignId": "campaign_id",
        "postalCode": "postal_code",
        "thirdParty": "third_party"
    }
    
    # Transform nested lists of objects
    if "addresses" in ts_data and ts_data["addresses"]:
        addresses = []
        for addr in ts_data["addresses"]:
            py_addr = {}
            for k, v in addr.items():
                py_addr[field_mappings.get(k, k)] = v
            addresses.append(py_addr)
        ts_data["addresses"] = addresses
    
    if "phones" in ts_data and ts_data["phones"]:
        phones = []
        for phone in ts_data["phones"]:
            py_phone = {}
            for k, v in phone.items():
                py_phone[field_mappings.get(k, k)] = v
            phones.append(py_phone)
        ts_data["phones"] = phones
    
    if "customFields" in ts_data:
        custom_fields = []
        for field in ts_data["customFields"]:
            py_field = {}
            for k, v in field.items():
                py_field[field_mappings.get(k, k)] = v
            custom_fields.append(py_field)
        ts_data["custom_fields"] = custom_fields
        del ts_data["customFields"]
    
    if "activity" in ts_data and ts_data["activity"]:
        activities = []
        for act in ts_data["activity"]:
            py_act = {}
            for k, v in act.items():
                py_act[field_mappings.get(k, k)] = v
            activities.append(py_act)
        ts_data["activity"] = activities
    
    # Transform consent data
    if "consent" in ts_data and ts_data["consent"]:
        consent = ts_data["consent"]
        py_consent = {}
        for k, v in consent.items():
            py_consent[field_mappings.get(k, k)] = v
        ts_data["consent"] = py_consent
    
    # Apply field mappings for top-level fields
    python_data = {}
    for key, value in ts_data.items():
        python_key = field_mappings.get(key, key)
        python_data[python_key] = value
    
    # Convert date strings to datetime objects
    date_fields = ["created_at", "updated_at", "last_activity"]
    for date_field in date_fields:
        if date_field in python_data and isinstance(python_data[date_field], str):
            python_data[date_field] = datetime.fromisoformat(python_data[date_field].replace("Z", "+00:00"))
    
    # Handle UUID fields
    uuid_fields = ["id", "organization_id"]
    for uuid_field in uuid_fields:
        if uuid_field in python_data and isinstance(python_data[uuid_field], str):
            python_data[uuid_field] = UUID(python_data[uuid_field])
    
    # Handle list of UUIDs
    if "list_ids" in python_data and isinstance(python_data["list_ids"], list):
        python_data["list_ids"] = [UUID(id_str) if isinstance(id_str, str) else id_str 
                                 for id_str in python_data["list_ids"]]
    
    # Create the Pydantic model
    return Contact(**python_data)


def to_ts_model(contact: Contact) -> Dict[str, Any]:
    """Convert Python Contact model to TypeScript compatible dict"""
    contact_dict = contact.dict()
    
    # Handle field name conversions (snake_case to camelCase)
    field_mappings = {
        "first_name": "firstName",
        "last_name": "lastName",
        "full_name": "fullName",
        "created_at": "createdAt",
        "updated_at": "updatedAt",
        "last_activity": "lastActivity",
        "profile_image": "profileImage",
        "organization_id": "organizationId",
        "list_ids": "listIds",
        "custom_fields": "customFields",
        "ip_address": "ipAddress",
        "user_agent": "userAgent",
        "campaign_id": "campaignId",
        "postal_code": "postalCode",
        "third_party": "thirdParty"
    }
    
    # Transform nested objects
    for collection_name in ["addresses", "phones", "activity"]:
        if collection_name in contact_dict and contact_dict[collection_name]:
            transformed_collection = []
            for item in contact_dict[collection_name]:
                ts_item = {}
                for k, v in item.items():
                    ts_key = field_mappings.get(k, k)
                    ts_item[ts_key] = v
                transformed_collection.append(ts_item)
            contact_dict[collection_name] = transformed_collection
    
    # Transform custom fields
    if "custom_fields" in contact_dict and contact_dict["custom_fields"]:
        custom_fields = []
        for field in contact_dict["custom_fields"]:
            ts_field = {}
            for k, v in field.items():
                ts_key = field_mappings.get(k, k)
                ts_field[ts_key] = v
            custom_fields.append(ts_field)
        contact_dict["customFields"] = custom_fields
        del contact_dict["custom_fields"]
    
    # Transform consent data
    if "consent" in contact_dict and contact_dict["consent"]:
        consent = contact_dict["consent"]
        ts_consent = {}
        for k, v in consent.items():
            ts_key = field_mappings.get(k, k)
            ts_consent[ts_key] = v
        contact_dict["consent"] = ts_consent
    
    # Apply field mappings for top-level fields
    ts_data = {}
    for key, value in contact_dict.items():
        if key in field_mappings:
            ts_data[field_mappings[key]] = value
        else:
            ts_data[key] = value
    
    # Convert datetime objects to ISO strings
    date_fields = ["createdAt", "updatedAt", "lastActivity"]
    for date_field in date_fields:
        if date_field in ts_data and isinstance(ts_data[date_field], datetime):
            ts_data[date_field] = ts_data[date_field].isoformat()
    
    # Convert UUID objects to strings
    uuid_fields = ["id", "organizationId"]
    for uuid_field in uuid_fields:
        if uuid_field in ts_data and isinstance(ts_data[uuid_field], UUID):
            ts_data[uuid_field] = str(ts_data[uuid_field])
    
    # Convert list of UUIDs to strings
    if "listIds" in ts_data and isinstance(ts_data["listIds"], list):
        ts_data["listIds"] = [str(id_obj) if isinstance(id_obj, UUID) else id_obj 
                            for id_obj in ts_data["listIds"]]
    
    # Handle nested date conversions
    if "activity" in ts_data and ts_data["activity"]:
        for activity in ts_data["activity"]:
            if "timestamp" in activity and isinstance(activity["timestamp"], datetime):
                activity["timestamp"] = activity["timestamp"].isoformat()
            if "campaignId" in activity and isinstance(activity["campaignId"], UUID):
                activity["campaignId"] = str(activity["campaignId"])
    
    if "consent" in ts_data and ts_data["consent"]:
        if "timestamp" in ts_data["consent"] and isinstance(ts_data["consent"]["timestamp"], datetime):
            ts_data["consent"]["timestamp"] = ts_data["consent"]["timestamp"].isoformat()
    
    return ts_data