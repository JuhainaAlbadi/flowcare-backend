from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.database import Base

class StaffRole(str, enum.Enum):
    admin = "admin"
    branch_manager = "branch_manager"
    staff = "staff"

class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(StaffRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Branch relationship
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    branch = relationship("Branch", back_populates="staff")

    # relationship
    appointments = relationship("Appointment", back_populates="staff")
    slots = relationship("Slot", back_populates="staff")