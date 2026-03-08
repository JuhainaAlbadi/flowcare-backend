from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.slot import Slot
from app.models.staff import Staff, StaffRole
from app.models.customer import Customer
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog, ActionType
from app.core.dependencies import require_admin, require_manager_or_admin, require_staff_or_above
from datetime import datetime, timezone
from enum import Enum as PyEnum

router = APIRouter(prefix="/admin", tags=["Admin"])

class StatusUpdate(str, PyEnum):
    checked_in = "checked_in"
    completed = "completed"
    no_show = "no_show"
    cancelled = "cancelled"

# ============ السلوتات ============
@router.post("/slots")
def create_slot(
    branch_id: int = Form(...),
    service_type_id: int = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    staff_id: int = Form(None),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    slot = Slot(
        branch_id=branch_id,
        service_type_id=service_type_id,
        start_time=datetime.fromisoformat(start_time),
        end_time=datetime.fromisoformat(end_time),
        staff_id=staff_id
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    log = AuditLog(
        action=ActionType.slot_created,
        actor_id=user_data["user"].id,
        actor_role=user_data["user"].role,
        entity_type="slot",
        entity_id=slot.id,
        branch_id=branch_id
    )
    db.add(log)
    db.commit()

    return {"message": "Slot created successfully ✅", "slot_id": slot.id}

@router.delete("/slots/{slot_id}")
def delete_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    slot = db.query(Slot).filter(Slot.id == slot_id, Slot.deleted_at == None).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found ❌")

    slot.deleted_at = datetime.now(timezone.utc)

    log = AuditLog(
        action=ActionType.slot_deleted,
        actor_id=user_data["user"].id,
        actor_role=user_data["user"].role,
        entity_type="slot",
        entity_id=slot_id,
        branch_id=slot.branch_id
    )
    db.add(log)
    db.commit()

    return {"message": "Slot deleted successfully ✅"}

# ============ المواعيد ============
@router.get("/appointments")
def list_appointments(
    db: Session = Depends(get_db),
    user_data = Depends(require_staff_or_above)
):
    user = user_data["user"]
    if user.role == StaffRole.admin:
        appointments = db.query(Appointment).all()
    elif user.role == StaffRole.branch_manager:
        appointments = db.query(Appointment).join(Slot).filter(
            Slot.branch_id == user.branch_id
        ).all()
    else:
        appointments = db.query(Appointment).filter(
            Appointment.staff_id == user.id
        ).all()

    return [{"id": a.id, "status": a.status, "customer_id": a.customer_id, "slot_id": a.slot_id} for a in appointments]

@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    status: StatusUpdate = Form(...),
    db: Session = Depends(get_db),
    user_data = Depends(require_staff_or_above)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")

    appointment.status = AppointmentStatus(status.value)

    log = AuditLog(
        action=ActionType.appointment_status_updated,
        actor_id=user_data["user"].id,
        actor_role=user_data["user"].role,
        entity_type="appointment",
        entity_id=appointment_id,
        branch_id=None
    )
    db.add(log)
    db.commit()

    return {"message": "Status updated successfully ✅", "status": status.value}

# ============ الزبائن ============
@router.get("/customers")
def list_customers(
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    customers = db.query(Customer).all()
    return [{"id": c.id, "full_name": c.full_name, "email": c.email, "phone": c.phone} for c in customers]

# ============ الـ Audit Log ============
@router.get("/audit-logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    user = user_data["user"]
    if user.role == StaffRole.admin:
        logs = db.query(AuditLog).all()
    else:
        logs = db.query(AuditLog).filter(AuditLog.branch_id == user.branch_id).all()

    return [{"id": l.id, "action": l.action, "actor_id": l.actor_id, "entity_type": l.entity_type, "entity_id": l.entity_id, "created_at": l.created_at} for l in logs]