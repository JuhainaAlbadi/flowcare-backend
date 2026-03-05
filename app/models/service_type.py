from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class ServiceType(Base):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    duration_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # الربط بالفرع
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    branch = relationship("Branch", back_populates="service_types")

    # العلاقات
    slots = relationship("Slot", back_populates="service_type")