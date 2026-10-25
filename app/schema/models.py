"""
Pydantic Schemas and Models
Defines all data models, Enums, and Literals for the application.
"""

from enum import Enum
from typing import Literal, Optional, Self
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


# ==========================================
# 1. Enums and Literals (Restricted Choices)
# ==========================================

# Enum: A class-based set of symbolic names bound to unique values
class ShipmentStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# Literal: Type hint that restricts a field to specific string values
CarrierChoice = Literal["BlueDart", "Delhivery", "FedEx"]


# ==========================================
# 2. Shipment Schemas
# ==========================================

class Shipment(BaseModel):
    """Full schema for a shipment"""
    id: int
    recipient: str = Field(min_length=2)
    phone: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.PENDING      # Uses Enum (Dropdown in Swagger!)
    items: list[str]
    weight_kg: float = Field(gt=0, description="Weight in kg, must be > 0")
    carrier: CarrierChoice                              # Uses Literal (Dropdown in Swagger!)


class ShipmentUpdate(BaseModel):
    """Schema for PATCH (all fields optional)"""
    recipient: str | None = None
    phone: str | None = None
    destination: str | None = None
    status: ShipmentStatus | None = None
    items: list[str] | None = None
    weight_kg: float | None = Field(default=None, gt=0)
    carrier: CarrierChoice | None = None


# ==========================================
# 3. Student & Contact Detail Schemas
# ==========================================

class ContactDetail(BaseModel):
    phone: str                                         # Validated by @field_validator below
    city: str                                          # Required string
    emergency_contact: Optional[str] = None            # Optional field

    # Field-level validator for phone number
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = value.strip()
        
        # Rule 1: Must start with '+' country code
        if not cleaned.startswith("+"):
            raise ValueError("Phone number must start with '+' (e.g. '+919511843388')")
        
        # Rule 2: Digits after '+' must only be numbers
        digits = cleaned[1:]
        if not digits.isdigit():
            raise ValueError("Phone number must only contain digits after '+'")
        
        # Rule 3: Length must be between 10 and 15 digits
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError("Phone number must be between 10 and 15 digits long")
        
        return cleaned


class Student(BaseModel):
    id: int                                            # Required
    name: str = Field(min_length=2)                    # Required, at least 2 chars
    email: EmailStr                                    # Validated by EmailStr & @field_validator below
    age: int = Field(gt=0, le=100)                     # Required, between 1 and 100
    course: str = "FastAPI Bootcamp"                   # Default string value
    is_enrolled: bool = True                           # Default boolean value

    # Optional and Nested Fields
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    interests: list[str] = Field(default_factory=list)
    contact_detail: Optional[ContactDetail] = None

    # Field-level validator for email
    @field_validator("email")
    @classmethod
    def validate_student_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        blocked_domains = ["tempmail.com", "fake.com", "throwaway.com"]
        domain = normalized.split("@")[-1]
        
        if domain in blocked_domains:
            raise ValueError(f"Domain '@{domain}' is not allowed for student registration")
        
        return normalized

    # Model-level validator: Cross-field check between 'age' and 'contact_detail'
    @model_validator(mode="after")
    def verify_minor_emergency_contact(self) -> Self:
        # Rule: Minor students (under 18) MUST provide an emergency contact
        if self.age < 18:
            if not self.contact_detail or not self.contact_detail.emergency_contact:
                raise ValueError(
                    "Students under 18 years old must provide an emergency contact number in contact_detail"
                )
        return self

