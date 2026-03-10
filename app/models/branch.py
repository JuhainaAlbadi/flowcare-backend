from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    location = Column(String, nullable=False)
    phone = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    staff = relationship("Staff", back_populates="branch")
    slots = relationship("Slot", back_populates="branch")
    service_types = relationship("ServiceType", back_populates="branch")