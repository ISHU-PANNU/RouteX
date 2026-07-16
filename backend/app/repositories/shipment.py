from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.shipment import Shipment, ShipmentStatus

class ShipmentRepository:
    def get(self, db: Session, id: int) -> Optional[Shipment]:
        return db.query(Shipment).filter(Shipment.id == id).first()

    def get_by_tracking_number(self, db: Session, tracking_number: str) -> Optional[Shipment]:
        return db.query(Shipment).filter(Shipment.tracking_number == tracking_number).first()

    def get_multi_with_filters(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ShipmentStatus] = None,
        agent_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> List[Shipment]:
        query = db.query(Shipment)
        if status:
            query = query.filter(Shipment.status == status)
        if agent_id is not None:
            query = query.filter(Shipment.delivery_agent_id == agent_id)
        if customer_id is not None:
            query = query.filter(Shipment.customer_id == customer_id)
        if search_query:
            query = query.filter(
                (Shipment.tracking_number.ilike(f"%{search_query}%")) |
                (Shipment.receiver_name.ilike(f"%{search_query}%")) |
                (Shipment.description.ilike(f"%{search_query}%"))
            )
        return query.offset(skip).limit(limit).all()

shipment_repository = ShipmentRepository()
