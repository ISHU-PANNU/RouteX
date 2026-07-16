from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import get_current_user, RoleChecker
from app.models.user import User, UserRole
from app.models.shipment import ShipmentStatus
from app.schemas.shipment import ShipmentBook, ShipmentOut, ShipmentUpdateStatus, ShipmentOTPVerify
from app.services.shipment import shipment_service
from app.core.exceptions import ForbiddenError

router = APIRouter(prefix="/shipments", tags=["Shipment Operations"])

@router.post(
    "/book", 
    response_model=ShipmentOut, 
    status_code=status.HTTP_201_CREATED,
    summary="Book Shipment",
    description="Enables customer profiles to submit courier requests. Coordinates are fetched using geocoding."
)
def book_shipment(
    book_in: ShipmentBook, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Customer]))
):
    return shipment_service.book_shipment(db, customer_id=current_user.id, book_in=book_in)

@router.get(
    "", 
    response_model=List[ShipmentOut],
    status_code=status.HTTP_200_OK,
    summary="Fetch All Shipments",
    description="Enables dashboards to search and filter shipments with security constraints."
)
def list_shipments(
    skip: int = 0,
    limit: int = 100,
    status: Optional[ShipmentStatus] = None,
    agent_id: Optional[int] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin, UserRole.Customer, UserRole.DeliveryAgent]))
):
    if current_user.role == UserRole.Customer:
        customer_id = current_user.id
        agent_id = None
    elif current_user.role == UserRole.DeliveryAgent:
        agent_id = current_user.id
        customer_id = None

    return shipment_service.list_shipments(
        db, skip=skip, limit=limit, status=status, 
        agent_id=agent_id, customer_id=customer_id, search_query=search
    )

@router.get(
    "/{id}", 
    response_model=ShipmentOut,
    status_code=status.HTTP_200_OK,
    summary="Get Shipment Details",
    description="Fetches full details of a specific package ID. Owners, dispatchers and assigned agents are permitted."
)
def get_shipment(
    id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    shipment = shipment_service.get_shipment_by_id(db, shipment_id=id)
    
    # Enforce Owner / Assigned / Admin RBAC
    is_owner = (shipment.customer_id == current_user.id)
    is_assigned = (shipment.delivery_agent_id == current_user.id)
    is_admin = (current_user.role == UserRole.Admin)
    
    if not (is_owner or is_assigned or is_admin):
        raise ForbiddenError("You do not have permission to view this shipment details.")
        
    return shipment

@router.patch(
    "/{id}/status", 
    response_model=ShipmentOut,
    status_code=status.HTTP_200_OK,
    summary="Update Shipment Status",
    description="Transitions package tracking states. Agents must scan correct QR hashes for Out For Delivery updates."
)
def update_status(
    id: int, 
    update_in: ShipmentUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin, UserRole.DeliveryAgent]))
):
    return shipment_service.update_status(
        db, shipment_id=id, update_in=update_in, actor_role=current_user.role
    )

@router.post(
    "/{id}/verify-otp", 
    response_model=ShipmentOut,
    status_code=status.HTTP_200_OK,
    summary="OTP Delivery Verification",
    description="Completes shipment delivery. Requires agent profiles to submit matching customer OTP codes."
)
def verify_otp(
    id: int, 
    otp_in: ShipmentOTPVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.DeliveryAgent]))
):
    return shipment_service.verify_otp_and_deliver(db, shipment_id=id, otp_code=otp_in.otp)
