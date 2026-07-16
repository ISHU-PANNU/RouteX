from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from app.models.shipment import ShipmentStatus

# Timeline tracking schemas

class LiveTrackingTimelineItem(BaseModel):
    status: ShipmentStatus
    timestamp: datetime
    remarks: Optional[str] = None

class LiveTrackingOut(BaseModel):
    tracking_number: str
    status: ShipmentStatus
    weight: Decimal
    description: Optional[str]
    recipient_name: str
    delivery_address: str
    timeline: List[LiveTrackingTimelineItem] = []
    two_stops_away_alert: bool = False
    otp_code: Optional[str] = None  # Shown only to authorized customer
    courier_lat: Optional[float] = None
    courier_lng: Optional[float] = None
    destination_lat: float
    destination_lng: float

