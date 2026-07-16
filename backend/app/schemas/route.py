from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.shipment import ShipmentStatus

class RouteOptimizeAndAssign(BaseModel):
    delivery_agent_id: int
    shipment_ids: List[int] = Field(..., min_items=1)

class RouteStopOut(BaseModel):
    id: int
    shipment_id: int
    sequence_index: int
    estimated_arrival: Optional[datetime] = None
    visited_at: Optional[datetime] = None
    delivery_address: str
    recipient_name: str
    lat: float
    lng: float
    status: ShipmentStatus

    class Config:
        from_attributes = True

class RouteOut(BaseModel):
    id: int
    delivery_agent_id: int
    date: date
    created_at: datetime
    stops: List[RouteStopOut] = []

    class Config:
        from_attributes = True

class RouteOptimizeResponse(BaseModel):
    route_id: int
    delivery_agent_id: int
    date: date
    sequence: List[RouteStopOut]

class RouteOptimizePreviewRequest(BaseModel):
    shipment_ids: List[int] = Field(..., min_items=1)

class StopPreview(BaseModel):
    shipment_id: int
    recipient_name: str
    delivery_address: str
    lat: float
    lng: float

class SavingsMetrics(BaseModel):
    original_distance_meters: float
    original_duration_seconds: float
    optimized_distance_meters: float
    optimized_duration_seconds: float
    distance_savings_meters: float
    duration_savings_seconds: float
    distance_savings_percent: float
    duration_savings_percent: float

class RouteOptimizePreviewResponse(BaseModel):
    depot_lat: float
    depot_lng: float
    depot_address: str
    stops: List[StopPreview]
    original_sequence: List[int]
    optimized_sequence: List[int]
    metrics: SavingsMetrics

