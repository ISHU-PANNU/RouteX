from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user_optional, RoleChecker
from app.models.user import User, UserRole
from app.schemas.tracking import LiveTrackingOut
from app.services.tracking import tracking_service

router = APIRouter(prefix="/tracking", tags=["Tracking & Geolocation"])

@router.get(
    "/{tracking_number}", 
    response_model=LiveTrackingOut,
    status_code=status.HTTP_200_OK,
    summary="Track Shipment",
    description="Fetches progress histories, status timelines and live locations of the courier. Reveals verification OTPs if the owner is logged in."
)
def track_shipment(
    tracking_number: str, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    current_user_id = current_user.id if current_user else None
    return tracking_service.track_shipment(db, tracking_number=tracking_number, current_user_id=current_user_id)
