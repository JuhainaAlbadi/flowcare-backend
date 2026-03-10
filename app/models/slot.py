from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Slot(Base):
    __tablename__ = "slots"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Soft Delete
    deleted_at = Column(DateTime, nullable=True)

    # Branch, service type, and staff relationships
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    service_type_id = Column(Integer, ForeignKey("service_types.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True)

    #relationship
    branch = relationship("Branch", back_populates="slots")
    service_type = relationship("ServiceType", back_populates="slots")
    staff = relationship("Staff", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)