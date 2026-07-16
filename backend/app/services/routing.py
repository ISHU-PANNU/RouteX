from datetime import date
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import BadRequestError, EntityNotFoundError
from app.core.routing_engine import solve_tsp_2opt, calculate_tour_cost
from app.models.route import Route, RouteStop
from app.models.shipment import Shipment, ShipmentStatus
from app.repositories.route import route_repository
from app.repositories.user import user_repository
from app.repositories.shipment import shipment_repository
from app.services.shipment import shipment_service
from app.utils.geo import get_distance_matrix

# Default Depot location coordinates (RouteX Central Warehouse Hub)
DEPOT_LAT = 37.7749
DEPOT_LNG = -122.4194
DEPOT_ADDRESS = "RouteX Central Warehouse Hub, 100 Depot Way, SF"

class RoutingService:
    def optimize_and_assign_route(
        self, 
        db: Session, 
        agent_id: int, 
        shipment_ids: List[int],
        run_date: date = None
    ) -> Route:
        if not run_date:
            run_date = date.today()
            
        # Verify delivery agent exists
        agent = user_repository.get(db, id=agent_id)
        if not agent or agent.role.value != "DeliveryAgent":
            raise EntityNotFoundError(f"Delivery agent with ID {agent_id} does not exist.")
            
        # Verify shipments are unassigned or at warehouse
        shipments: List[Shipment] = []
        for sid in shipment_ids:
            shipment = shipment_repository.get(db, id=sid)
            if not shipment:
                raise EntityNotFoundError(f"Shipment with ID {sid} does not exist.")
            if shipment.status in [ShipmentStatus.DELIVERED]:
                raise BadRequestError(f"Shipment {sid} has already been delivered.")
            shipments.append(shipment)
            
        # Check if agent already has an active route today
        existing_route = route_repository.get_route_by_agent_and_date(db, agent_id=agent_id, run_date=run_date)
        if existing_route:
            raise BadRequestError(f"Agent already has an assigned route schedule for {run_date}.")

        # Compile coordinates array: Depot at index 0, followed by shipment coordinates
        coords = [(DEPOT_LAT, DEPOT_LNG)]
        for s in shipments:
            coords.append((float(s.delivery_lat), float(s.delivery_lng)))
            
        # Fetch distance matrix
        distances, durations = get_distance_matrix(coords)
        
        # Calculate optimized cost using 2-opt TSP routing engine
        optimized_tour, _ = solve_tsp_2opt(distances)
        
        # Create route entry
        db_route = Route(
            delivery_agent_id=agent_id,
            date=run_date
        )
        db.add(db_route)
        db.commit()
        db.refresh(db_route)
        
        # Create RouteStop entries based on optimized tour indices
        # Note: optimized_tour format: [0, stop1, stop2, ..., 0]
        # We omit index 0 (the depot starting/ending point) when saving delivery sequence stops
        sequence_index = 1
        for node in optimized_tour[1:-1]:
            shipment_index = node - 1 # Map node index back to shipments array
            shipment = shipments[shipment_index]
            
            # Save waypoint
            stop = RouteStop(
                route_id=db_route.id,
                shipment_id=shipment.id,
                sequence_index=sequence_index
            )
            db.add(stop)
            
            # Update shipment to Assigned status and link agent
            shipment.status = ShipmentStatus.ASSIGNED_TO_DELIVERY_AGENT
            shipment.delivery_agent_id = agent_id
            
            # Log progress
            shipment_service._add_status_history(
                db, 
                shipment.id, 
                ShipmentStatus.ASSIGNED_TO_DELIVERY_AGENT, 
                f"Assigned to agent {agent.name}. Stop sequence index: #{sequence_index}"
            )
            sequence_index += 1
            
        db.commit()
        db.refresh(db_route)
        return db_route

    def preview_optimized_route(
        self,
        db: Session,
        shipment_ids: List[int]
    ):
        # Fetch shipments
        shipments: List[Shipment] = []
        for sid in shipment_ids:
            shipment = shipment_repository.get(db, id=sid)
            if not shipment:
                raise EntityNotFoundError(f"Shipment with ID {sid} does not exist.")
            if shipment.status in [ShipmentStatus.DELIVERED]:
                raise BadRequestError(f"Shipment {sid} has already been delivered.")
            shipments.append(shipment)
            
        n = len(shipments)
        if n == 0:
            raise BadRequestError("No shipments provided for optimization.")
            
        # Compile coordinates array: Depot at index 0, followed by shipment coordinates
        coords = [(DEPOT_LAT, DEPOT_LNG)]
        for s in shipments:
            coords.append((float(s.delivery_lat), float(s.delivery_lng)))
            
        # Fetch distance matrix
        distances, durations = get_distance_matrix(coords)
        
        # Calculate original tour (Depot -> 1 -> 2 -> ... -> N -> Depot)
        original_tour = [0] + list(range(1, n + 1)) + [0]
        original_dist = calculate_tour_cost(original_tour, distances)
        original_dur = calculate_tour_cost(original_tour, durations)
        
        # Calculate optimized tour using TSP solver
        optimized_tour, optimized_dist = solve_tsp_2opt(distances)
        optimized_dur = calculate_tour_cost(optimized_tour, durations)
        
        # Calculate savings
        dist_savings = max(0.0, float(original_dist - optimized_dist))
        dur_savings = max(0.0, float(original_dur - optimized_dur))
        
        dist_savings_pct = (dist_savings / original_dist * 100.0) if original_dist > 0 else 0.0
        dur_savings_pct = (dur_savings / original_dur * 100.0) if original_dur > 0 else 0.0
        
        # Build stops preview info
        from app.schemas.route import StopPreview, SavingsMetrics, RouteOptimizePreviewResponse
        stops_preview = []
        for s in shipments:
            stops_preview.append(
                StopPreview(
                    shipment_id=s.id,
                    recipient_name=s.receiver_name,
                    delivery_address=s.delivery_address,
                    lat=float(s.delivery_lat),
                    lng=float(s.delivery_lng)
                )
            )
            
        return RouteOptimizePreviewResponse(
            depot_lat=DEPOT_LAT,
            depot_lng=DEPOT_LNG,
            depot_address=DEPOT_ADDRESS,
            stops=stops_preview,
            original_sequence=original_tour,
            optimized_sequence=optimized_tour,
            metrics=SavingsMetrics(
                original_distance_meters=float(original_dist),
                original_duration_seconds=float(original_dur),
                optimized_distance_meters=float(optimized_dist),
                optimized_duration_seconds=float(optimized_dur),
                distance_savings_meters=dist_savings,
                duration_savings_seconds=dur_savings,
                distance_savings_percent=round(dist_savings_pct, 2),
                duration_savings_percent=round(dur_savings_pct, 2)
            )
        )

    def get_agent_active_route(self, db: Session, agent_id: int, run_date: date = None) -> Optional[Route]:
        if not run_date:
            run_date = date.today()
        return route_repository.get_route_by_agent_and_date(db, agent_id=agent_id, run_date=run_date)

routing_service = RoutingService()
