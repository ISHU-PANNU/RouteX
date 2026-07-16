import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class UserRole(str, enum.Enum):
    Customer = "Customer"
    DeliveryAgent = "DeliveryAgent"
    Admin = "Admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    role = Column(Enum(UserRole), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    shipments_booked = relationship("Shipment", back_populates="customer", foreign_keys="[Shipment.customer_id]")
    shipments_assigned = relationship("Shipment", back_populates="delivery_agent", foreign_keys="[Shipment.delivery_agent_id]")
    routes = relationship("Route", back_populates="delivery_agent", cascade="all, delete-orphan")
