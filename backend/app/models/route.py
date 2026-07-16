from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    delivery_agent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    delivery_agent = relationship("User", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.sequence_index")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    
    sequence_index = Column(Integer, nullable=False) # e.g. 1, 2, 3...
    estimated_arrival = Column(DateTime, nullable=True)
    visited_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    route = relationship("Route", back_populates="stops")
    shipment = relationship("Shipment", back_populates="route_stops")

    __table_args__ = (
        UniqueConstraint("route_id", "sequence_index", name="uq_route_sequence"),
    )
