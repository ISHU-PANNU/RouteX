from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.shipment import ShipmentStatus
from app.database.base_class import Base

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ShipmentStatus), nullable=False)
    remarks = Column(String(255), nullable=True)
    changed_at = Column(DateTime, server_default=func.now())

    # Relationships
    shipment = relationship("Shipment", back_populates="status_history")
