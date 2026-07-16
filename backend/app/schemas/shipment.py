from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, field_validator
from app.models.shipment import ShipmentStatus
from app.schemas.auth import PHONE_REGEX

class ShipmentBook(BaseModel):
    weight: Decimal = Field(..., ge=Decimal("0.1"), le=Decimal("500.0"))
    length_cm: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("300.0"))
    width_cm: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("300.0"))
    height_cm: Optional[Decimal] = Field(None, ge=Decimal("1.0"), le=Decimal("300.0"))
    description: Optional[str] = Field(None, max_length=1000)
    
    pickup_address: str = Field(..., min_length=10, max_length=500)
    delivery_address: str = Field(..., min_length=10, max_length=500)
    
    receiver_name: str = Field(..., min_length=2, max_length=100)
    receiver_phone: str = Field(...)
    receiver_email: EmailStr

    @field_validator("receiver_phone")
    @classmethod
    def validate_receiver_phone(cls, v: str) -> str:
        clean_phone = v.replace(" ", "").replace("-", "")
        if not PHONE_REGEX.match(clean_phone):
            raise ValueError("Recipient phone number must match standard E.164 format.")
        return clean_phone

class ShipmentUpdateStatus(BaseModel):
    status: ShipmentStatus
    qr_payload: Optional[str] = None

class ShipmentOTPVerify(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("otp")
    @classmethod
    def validate_otp_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP code must consist of exactly 6 numeric digits.")
        return v

class StatusHistoryOut(BaseModel):
    status: ShipmentStatus
    remarks: Optional[str]
    changed_at: datetime

    class Config:
        from_attributes = True

class ShipmentOut(BaseModel):
    id: int
    tracking_number: str
    customer_id: int
    delivery_agent_id: Optional[int]
    weight: Decimal
    length_cm: Optional[Decimal]
    width_cm: Optional[Decimal]
    height_cm: Optional[Decimal]
    description: Optional[str]
    pickup_address: str
    pickup_lat: Decimal
    pickup_lng: Decimal
    delivery_address: str
    delivery_lat: Decimal
    delivery_lng: Decimal
    status: ShipmentStatus
    created_at: datetime
    updated_at: datetime
    status_history: List[StatusHistoryOut] = []

    class Config:
        from_attributes = True
