from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from app.models.route import Route, RouteStop

class RouteRepository:
    def get(self, db: Session, id: int) -> Optional[Route]:
        return db.query(Route).filter(Route.id == id).first()

    def get_route_by_agent_and_date(self, db: Session, agent_id: int, run_date: date) -> Optional[Route]:
        return db.query(Route).filter(
            Route.delivery_agent_id == agent_id,
            Route.date == run_date
        ).first()

class RouteStopRepository:
    def get(self, db: Session, id: int) -> Optional[RouteStop]:
        return db.query(RouteStop).filter(RouteStop.id == id).first()

    def get_stop_by_shipment(self, db: Session, shipment_id: int) -> Optional[RouteStop]:
        return db.query(RouteStop).filter(RouteStop.shipment_id == shipment_id).first()

route_repository = RouteRepository()
route_stop_repository = RouteStopRepository()
