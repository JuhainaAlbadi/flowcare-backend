from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum
from datetime import datetime, timezone
import enum
from app.database import Base

class ActionType(str, enum.Enum):
    appointment_created = "appointment_created"
    appointment_cancelled = "appointment_cancelled"
    appointment_rescheduled = "appointment_rescheduled"
    appointment_status_updated = "appointment_status_updated"
    slot_created = "slot_created"
    slot_updated = "slot_updated"
    slot_deleted = "slot_deleted"
    slot_hard_deleted = "slot_hard_deleted"
    staff_assigned = "staff_assigned"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(Enum(ActionType), nullable=False)
    actor_id = Column(Integer, nullable=False)
    actor_role = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    extra_data  = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))