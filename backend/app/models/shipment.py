import enum
from sqlalchemy import Column, Integer, String, Enum, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class ShipmentStatus(str, enum.Enum):
    ORDER_RECEIVED = "Order Received"
    PACKED = "Packed"
    AT_WAREHOUSE = "At Warehouse"
    ASSIGNED_TO_DELIVERY_AGENT = "Assigned to Delivery Agent"
    OUT_FOR_DELIVERY = "Out For Delivery"
    TWO_STOPS_AWAY = "Two Stops Away"
    DELIVERED = "Delivered"

class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(64), nullable=False, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    delivery_agent_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Cargo Details
    weight = Column(Numeric(8, 2), nullable=False) # in Kg
    length_cm = Column(Numeric(6, 2), nullable=True)
    width_cm = Column(Numeric(6, 2), nullable=True)
    height_cm = Column(Numeric(6, 2), nullable=True)
    description = Column(Text, nullable=True)

    # Pickup Coordinates
    pickup_address = Column(Text, nullable=False)
    pickup_lat = Column(Numeric(10, 8), nullable=False)
    pickup_lng = Column(Numeric(11, 8), nullable=False)

    # Delivery Destination Coordinates
    delivery_address = Column(Text, nullable=False)
    delivery_lat = Column(Numeric(10, 8), nullable=False)
    delivery_lng = Column(Numeric(11, 8), nullable=False)

    # Receiver details
    receiver_name = Column(String(255), nullable=False)
    receiver_phone = Column(String(20), nullable=False)
    receiver_email = Column(String(255), nullable=False)

    # QR Scan Matching Hash
    qr_code_hash = Column(String(255), nullable=False)
    
    # 6-Digit Verification OTP
    otp_code = Column(String(6), nullable=False)
    otp_verified_at = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(Enum(ShipmentStatus), nullable=False, default=ShipmentStatus.ORDER_RECEIVED, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("User", back_populates="shipments_booked", foreign_keys=[customer_id])
    delivery_agent = relationship("User", back_populates="shipments_assigned", foreign_keys=[delivery_agent_id])
    status_history = relationship("StatusHistory", back_populates="shipment", cascade="all, delete-orphan")
    route_stops = relationship("RouteStop", back_populates="shipment", cascade="all, delete-orphan")
