import random
import string
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import EntityNotFoundError, VerificationFailedError, BadRequestError
from app.models.shipment import Shipment, ShipmentStatus
from app.models.status_history import StatusHistory
from app.models.user import UserRole
from app.repositories.shipment import shipment_repository
from app.schemas.shipment import ShipmentBook, ShipmentUpdateStatus
from app.utils.geo import geocode_address

def generate_tracking_number() -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_hash = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"RP-{date_str}-{random_hash}"

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))

class ShipmentService:
    def book_shipment(self, db: Session, customer_id: int, book_in: ShipmentBook) -> Shipment:
        tracking_number = generate_tracking_number()
        
        # Geocode pickup and delivery addresses
        pickup_lat, pickup_lng = geocode_address(book_in.pickup_address)
        delivery_lat, delivery_lng = geocode_address(book_in.delivery_address)
        
        # Generate QR Hash and OTP Code
        qr_code_hash = hashlib.sha256(f"QR-{tracking_number}".encode("utf-8")).hexdigest()
        otp_code = generate_otp()
        
        db_shipment = Shipment(
            tracking_number=tracking_number,
            customer_id=customer_id,
            weight=book_in.weight,
            length_cm=book_in.length_cm,
            width_cm=book_in.width_cm,
            height_cm=book_in.height_cm,
            description=book_in.description,
            pickup_address=book_in.pickup_address,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            delivery_address=book_in.delivery_address,
            delivery_lat=delivery_lat,
            delivery_lng=delivery_lng,
            receiver_name=book_in.receiver_name,
            receiver_phone=book_in.receiver_phone,
            receiver_email=book_in.receiver_email,
            qr_code_hash=qr_code_hash,
            otp_code=otp_code,
            status=ShipmentStatus.ORDER_RECEIVED
        )
        
        db.add(db_shipment)
        db.commit()
        db.refresh(db_shipment)
        
        # Add initial status history log
        self._add_status_history(db, db_shipment.id, ShipmentStatus.ORDER_RECEIVED, "Shipment booked successfully.")
        
        return db_shipment

    def get_shipment_by_id(self, db: Session, shipment_id: int) -> Shipment:
        shipment = shipment_repository.get(db, id=shipment_id)
        if not shipment:
            raise EntityNotFoundError(f"Shipment with ID {shipment_id} does not exist.")
        return shipment

    def get_shipment_by_tracking(self, db: Session, tracking_number: str) -> Shipment:
        shipment = shipment_repository.get_by_tracking_number(db, tracking_number=tracking_number)
        if not shipment:
            raise EntityNotFoundError(f"Shipment with tracking number {tracking_number} does not exist.")
        return shipment

    def list_shipments(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ShipmentStatus] = None,
        agent_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        search_query: Optional[str] = None
    ) -> List[Shipment]:
        return shipment_repository.get_multi_with_filters(
            db,
            skip=skip,
            limit=limit,
            status=status,
            agent_id=agent_id,
            customer_id=customer_id,
            search_query=search_query
        )

    def update_status(
        self,
        db: Session,
        shipment_id: int,
        update_in: ShipmentUpdateStatus,
        actor_role: UserRole
    ) -> Shipment:
        shipment = self.get_shipment_by_id(db, shipment_id)
        
        # Guard rules for transitions
        new_status = update_in.status
        
        # Agent role verification controls for QR code scanning
        if actor_role == UserRole.DeliveryAgent:
            if new_status == ShipmentStatus.OUT_FOR_DELIVERY:
                if not update_in.qr_payload:
                    raise VerificationFailedError("QR scan payload required for Out For Delivery transition.")
                
                # Check QR Hash payload matches
                expected_hash = hashlib.sha256(f"QR-{shipment.tracking_number}".encode("utf-8")).hexdigest()
                if update_in.qr_payload != expected_hash and update_in.qr_payload != shipment.tracking_number:
                    raise VerificationFailedError("Scanned QR code does not match shipment signature.")
            else:
                # Agents cannot arbitrarily execute state changes (e.g. Packed)
                if new_status not in [ShipmentStatus.OUT_FOR_DELIVERY, ShipmentStatus.TWO_STOPS_AWAY, ShipmentStatus.DELIVERED]:
                    raise BadRequestError(f"Delivery Agent cannot change status to {new_status.value}")

        # Update shipment status
        shipment.status = new_status
        db.commit()
        db.refresh(shipment)
        
        self._add_status_history(db, shipment.id, new_status, f"Status updated to {new_status.value} by {actor_role.value}")

        # If shipment transitions to Out For Delivery, trigger proximity evaluation for route
        if new_status == ShipmentStatus.OUT_FOR_DELIVERY:
            from app.repositories.route import route_stop_repository
            from app.services.tracking import tracking_service
            stop = route_stop_repository.get_stop_by_shipment(db, shipment_id=shipment.id)
            if stop:
                tracking_service.evaluate_proximity_alerts(db, route_id=stop.route_id)

        return shipment

    def verify_otp_and_deliver(self, db: Session, shipment_id: int, otp_code: str) -> Shipment:
        shipment = self.get_shipment_by_id(db, shipment_id)
        
        if shipment.status == ShipmentStatus.DELIVERED:
            raise BadRequestError("Shipment is already delivered.")
            
        if shipment.otp_code != otp_code:
            raise VerificationFailedError("Provided verification OTP is incorrect.")
            
        shipment.status = ShipmentStatus.DELIVERED
        shipment.otp_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        db.refresh(shipment)
        
        self._add_status_history(db, shipment.id, ShipmentStatus.DELIVERED, "OTP verification successful. Package delivered.")
        
        # Mark stop as visited and trigger proximity evaluation
        from app.repositories.route import route_stop_repository
        from app.services.tracking import tracking_service
        
        stop = route_stop_repository.get_stop_by_shipment(db, shipment_id=shipment.id)
        if stop:
            stop.visited_at = datetime.now(timezone.utc).replace(tzinfo=None)
            db.commit()
            tracking_service.evaluate_proximity_alerts(db, route_id=stop.route_id)
            
        return shipment

    def _add_status_history(self, db: Session, shipment_id: int, status: ShipmentStatus, remarks: str) -> None:
        log = StatusHistory(
            shipment_id=shipment_id,
            status=status,
            remarks=remarks
        )
        db.add(log)
        db.commit()

shipment_service = ShipmentService()
