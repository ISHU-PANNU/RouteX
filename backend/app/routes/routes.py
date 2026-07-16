from datetime import date
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies.db import get_db
from app.dependencies.auth import RoleChecker
from app.models.user import User, UserRole
from app.schemas.route import RouteOptimizeAndAssign, RouteOptimizeResponse, RouteStopOut, RouteOut, RouteOptimizePreviewRequest, RouteOptimizePreviewResponse
from app.services.routing import routing_service
from app.core.exceptions import EntityNotFoundError

router = APIRouter(prefix="/routes", tags=["Route Planning"])

@router.post(
    "/optimize-and-assign", 
    response_model=RouteOptimizeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Optimize and Assign Route",
    description="Resolves TSP coordinates sequence optimizations using 2-opt search, registers routes and assigns stops to agents."
)
def optimize_and_assign(
    assign_in: RouteOptimizeAndAssign, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin]))
):
    db_route = routing_service.optimize_and_assign_route(
        db, 
        agent_id=assign_in.delivery_agent_id, 
        shipment_ids=assign_in.shipment_ids
    )
    
    # Map database Route entities to Schema response
    sequence = []
    for stop in db_route.stops:
        shipment = stop.shipment
        sequence.append(
            RouteStopOut(
                id=stop.id,
                shipment_id=stop.shipment_id,
                sequence_index=stop.sequence_index,
                estimated_arrival=stop.estimated_arrival,
                visited_at=stop.visited_at,
                delivery_address=shipment.delivery_address,
                recipient_name=shipment.receiver_name,
                lat=float(shipment.delivery_lat),
                lng=float(shipment.delivery_lng),
                status=shipment.status
            )
        )
        
    return RouteOptimizeResponse(
        route_id=db_route.id,
        delivery_agent_id=db_route.delivery_agent_id,
        date=db_route.date,
        sequence=sequence
    )

@router.get(
    "/agent/today", 
    response_model=RouteOut,
    status_code=status.HTTP_200_OK,
    summary="Get Today's Route Stops",
    description="Returns the active optimized stops queue assigned to the requesting courier profile."
)
def get_today_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.DeliveryAgent]))
):
    db_route = routing_service.get_agent_active_route(db, agent_id=current_user.id)
    if not db_route:
        raise EntityNotFoundError("No active delivery route schedules found today.")
        
    # Build stops list structure sorted by shipment_id (original booking sequence)
    # This prevents the delivery agent from seeing the optimized route sequence
    sorted_stops = sorted(db_route.stops, key=lambda s: s.shipment_id)
    stops_list = []
    for idx, stop in enumerate(sorted_stops, start=1):
        shipment = stop.shipment
        stops_list.append(
            RouteStopOut(
                id=stop.id,
                shipment_id=stop.shipment_id,
                sequence_index=idx,
                estimated_arrival=stop.estimated_arrival,
                visited_at=stop.visited_at,
                delivery_address=shipment.delivery_address,
                recipient_name=shipment.receiver_name,
                lat=float(shipment.delivery_lat),
                lng=float(shipment.delivery_lng),
                status=shipment.status
            )
        )
        
    return RouteOut(
        id=db_route.id,
        delivery_agent_id=db_route.delivery_agent_id,
        date=db_route.date,
        created_at=db_route.created_at,
        stops=stops_list
    )

@router.post(
    "/optimize-preview",
    response_model=RouteOptimizePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview Route Optimization",
    description="Compares the original sequence with the optimized tour, returns coords and savings metrics before assignment."
)
def optimize_preview(
    preview_in: RouteOptimizePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.Admin]))
):
    return routing_service.preview_optimized_route(db, shipment_ids=preview_in.shipment_ids)

