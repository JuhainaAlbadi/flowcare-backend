from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    hashed_password = Column(String, nullable=False)
    id_image_path = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # العلاقات
    appointments = relationship("Appointment", back_populates="customer")