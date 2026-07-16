from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundError, BadRequestError
from app.models.route import Route, RouteStop
from app.models.shipment import Shipment, ShipmentStatus
from app.repositories.shipment import shipment_repository
from app.repositories.route import route_repository, route_stop_repository
from app.schemas.tracking import LiveTrackingOut, LiveTrackingTimelineItem
from app.services.shipment import shipment_service

class TrackingService:
    def evaluate_proximity_alerts(self, db: Session, route_id: int) -> None:
        """
        Evaluate if any remaining stop on the route is exactly 2 stops away from the completed stops.
        The active sequence of stops is sorted by shipment_id (original booking sequence).
        """
        stops = db.query(RouteStop).filter(RouteStop.route_id == route_id).all()
        if not stops:
            return
            
        sorted_stops = sorted(stops, key=lambda s: s.shipment_id)
        
        # Find the index of the first unvisited stop
        first_unvisited_idx = -1
        for idx, stop in enumerate(sorted_stops):
            if stop.visited_at is None:
                first_unvisited_idx = idx
                break
                
        if first_unvisited_idx != -1:
            # The stop at first_unvisited_idx is 1 stop away (the active target).
            # The stop at first_unvisited_idx + 1 is 2 stops away.
            target_idx = first_unvisited_idx + 1
            if target_idx < len(sorted_stops):
                target_stop = sorted_stops[target_idx]
                shipment = target_stop.shipment
                if shipment.status in [ShipmentStatus.ASSIGNED_TO_DELIVERY_AGENT, ShipmentStatus.OUT_FOR_DELIVERY]:
                    shipment.status = ShipmentStatus.TWO_STOPS_AWAY
                    db.commit()
                    
                    # Log status history
                    shipment_service._add_status_history(
                        db, 
                        shipment.id, 
                        ShipmentStatus.TWO_STOPS_AWAY, 
                        "Agent is now 2 stops away from this delivery destination."
                    )

    def track_shipment(self, db: Session, tracking_number: str, current_user_id: Optional[int] = None) -> LiveTrackingOut:
        shipment = shipment_repository.get_by_tracking_number(db, tracking_number=tracking_number)
        if not shipment:
            raise EntityNotFoundError(f"Tracking ID {tracking_number} is invalid.")
            
        # Fetch status history logs
        timeline = []
        for log in shipment.status_history:
            timeline.append(
                LiveTrackingTimelineItem(
                    status=log.status,
                    timestamp=log.changed_at,
                    remarks=log.remarks
                )
            )
            
        # Proximity alert boolean flag
        two_stops_away = (shipment.status == ShipmentStatus.TWO_STOPS_AWAY)
        
        # Display OTP code only if user is authorized customer
        otp_code = None
        if current_user_id and current_user_id == shipment.customer_id:
            otp_code = shipment.otp_code

        # Determine destination coordinates
        destination_lat = float(shipment.delivery_lat)
        destination_lng = float(shipment.delivery_lng)

        # Simulate courier live location based on active route progress
        courier_lat = None
        courier_lng = None
        route_stop = shipment.route_stops[0] if shipment.route_stops else None
        if route_stop:
            route = route_stop.route
            stops = db.query(RouteStop).filter(RouteStop.route_id == route.id).all()
            sorted_stops = sorted(stops, key=lambda s: s.shipment_id)
            
            # Find the last visited stop
            last_visited = None
            for s in sorted_stops:
                if s.visited_at is not None:
                    last_visited = s
            
            if last_visited:
                courier_lat = float(last_visited.shipment.delivery_lat)
                courier_lng = float(last_visited.shipment.delivery_lng)
            else:
                # If no stops visited but route has active deliveries, courier is at depot
                is_active = any(
                    s.shipment.status in [ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.TWO_STOPS_AWAY, ShipmentStatus.DELIVERED]
                    for s in sorted_stops
                )
                if is_active:
                    from app.services.routing import DEPOT_LAT, DEPOT_LNG
                    courier_lat = DEPOT_LAT
                    courier_lng = DEPOT_LNG

        return LiveTrackingOut(
            tracking_number=shipment.tracking_number,
            status=shipment.status,
            weight=shipment.weight,
            description=shipment.description,
            recipient_name=shipment.receiver_name if hasattr(shipment, "receiver_name") else "Recipient",
            delivery_address=shipment.delivery_address,
            timeline=timeline,
            two_stops_away_alert=two_stops_away,
            otp_code=otp_code,
            destination_lat=destination_lat,
            destination_lng=destination_lng,
            courier_lat=courier_lat,
            courier_lng=courier_lng
        )

tracking_service = TrackingService()
