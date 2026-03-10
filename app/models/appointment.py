from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base

class AppointmentStatus(str, enum.Enum):
    booked = "booked"
    checked_in = "checked_in"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.booked)
    notes = Column(String, nullable=True)
    attachment_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)

  
    slot = relationship("Slot", back_populates="appointment")
    customer = relationship("Customer", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")