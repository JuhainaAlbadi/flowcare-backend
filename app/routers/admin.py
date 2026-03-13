from fastapi import APIRouter, Depends, HTTPException, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.slot import Slot
from app.models.staff import Staff, StaffRole
from app.models.customer import Customer
from app.models.appointment import Appointment, AppointmentStatus
from app.models.audit_log import AuditLog, ActionType
from app.core.dependencies import require_admin, require_manager_or_admin, require_staff_or_above,get_authenticated_user
from datetime import datetime, timezone, timedelta
from enum import Enum as PyEnum
import csv
import io
from fastapi.responses import StreamingResponse,FileResponse
from sqlalchemy import text
import os

router = APIRouter(prefix="/admin", tags=["Admin"])

class StatusUpdate(str, PyEnum):
    checked_in = "checked_in"
    completed = "completed"
    no_show = "no_show"
    cancelled = "cancelled"

# ============ slots============
@router.post("/slots")
def create_slot(
    branch_id: int = Form(...),
    service_type_id: int = Form(...),
    start_times: str = Form(...),
    end_times: str = Form(...),
    staff_id: int = Form(None),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    # Split by comma for bulk creation
    start_list = [s.strip() for s in start_times.split(",")]
    end_list = [e.strip() for e in end_times.split(",")]

    if len(start_list) != len(end_list):
        raise HTTPException(status_code=400, detail="start_times and end_times must have same count ❌")

    created = []
    for start, end in zip(start_list, end_list):
        slot = Slot(
            branch_id=branch_id,
            service_type_id=service_type_id,
            start_time=datetime.fromisoformat(start),
            end_time=datetime.fromisoformat(end),
            staff_id=staff_id
        )
        db.add(slot)
        db.flush()

        log = AuditLog(
            action=ActionType.slot_created,
            actor_id=user_data["user"].id,
            actor_role=user_data["user"].role,
            entity_type="slot",
            entity_id=slot.id,
            branch_id=branch_id
        )
        db.add(log)
        created.append(slot.id)

    db.commit()
    return {"message": f"{len(created)} slot(s) created successfully ✅", "slot_ids": created}

@router.get("/slots/deleted")
def list_deleted_slots(
    db: Session = Depends(get_db),
    user_data = Depends(require_admin)
):
    slots = db.query(Slot).filter(Slot.deleted_at != None).all()
    return [
        {
            "id": s.id,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "branch_id": s.branch_id,
            "service_type_id": s.service_type_id,
            "deleted_at": s.deleted_at
        } for s in slots
    ]


@router.delete("/slots/hard-delete-cleanup")
def cleanup_soft_deleted(
    db: Session = Depends(get_db),
    user_data = Depends(require_admin)
):
    # Get the retention period
    try:
        result = db.execute(text("SELECT value FROM settings WHERE key = 'retention_days'")).fetchone()
        retention_days = int(result[0]) if result else 30
    except:
        db.rollback()
        retention_days = 30

    # Get slots that exceeded the retention period
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_slots = db.query(Slot).filter(
        Slot.deleted_at != None,
        Slot.deleted_at <= cutoff
    ).all()

    count = 0
    for slot in old_slots:
        # Handle related appointments - set slot_id to null
        related_appointments = db.query(Appointment).filter(
            Appointment.slot_id == slot.id
        ).all()
        for appointment in related_appointments:
            appointment.slot_id = None

        # Log the hard delete action
        log = AuditLog(
            action=ActionType.slot_hard_deleted,
            actor_id=user_data["user"].id,
            actor_role=user_data["user"].role,
            entity_type="slot",
            entity_id=slot.id,
            branch_id=slot.branch_id
        )
        db.add(log)
        db.delete(slot)
        count += 1

    db.commit()
    return {"message": f"Cleaned up {count} slots successfully ✅"}

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

@router.put("/slots/{slot_id}")
def update_slot(
    slot_id: int,
    start_time: str = Form(None),
    end_time: str = Form(None),
    staff_id: int = Form(None),
    is_available: bool = Form(None),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    slot = db.query(Slot).filter(
        Slot.id == slot_id,
        Slot.deleted_at == None
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found ❌")

    # Update only provided fields
    if start_time:
        slot.start_time = datetime.fromisoformat(start_time)
    if end_time:
        slot.end_time = datetime.fromisoformat(end_time)
    if staff_id is not None:
        slot.staff_id = staff_id
    if is_available is not None:
        slot.is_available = is_available

    # Log the update
    log = AuditLog(
        action=ActionType.slot_updated,
        actor_id=user_data["user"].id,
        actor_role=user_data["user"].role,
        entity_type="slot",
        entity_id=slot_id,
        branch_id=slot.branch_id
    )
    db.add(log)
    db.commit()

    return {"message": "Slot updated successfully ✅", "slot_id": slot_id}


# ============ appoinments ============
@router.get("/appointments")
def list_appointments(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_data = Depends(require_staff_or_above)
):
    user = user_data["user"]
    if user.role == StaffRole.admin:
        query = db.query(Appointment)
    elif user.role == StaffRole.branch_manager:
        query = db.query(Appointment).join(Slot).filter(
            Slot.branch_id == user.branch_id
        )
    else:
        query = db.query(Appointment).filter(
            Appointment.staff_id == user.id
        )

    if search:
        query = query.join(Customer).filter(
            Customer.full_name.ilike(f"%{search}%") |
            Customer.email.ilike(f"%{search}%")
        )

    total = query.count()
    appointments = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": [{"id": a.id, "status": a.status, "customer_id": a.customer_id, "slot_id": a.slot_id, "notes": a.notes} for a in appointments]
    }

@router.put("/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    status: StatusUpdate = Form(...),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    user_data = Depends(require_staff_or_above)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")

    appointment.status = AppointmentStatus(status.value)
    
    # Add internal notes if provided
    if notes:
        appointment.notes = notes

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

# ============ customers ============
@router.get("/customers")
def list_customers(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    query = db.query(Customer)
    if search:
        query = query.filter(
            Customer.full_name.ilike(f"%{search}%") |
            Customer.email.ilike(f"%{search}%")
        )
    total = query.count()
    customers = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": [{"id": c.id, "full_name": c.full_name, "email": c.email, "phone": c.phone} for c in customers]
    }

@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found ❌")

    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "email": customer.email,
        "phone": customer.phone,
        "is_active": customer.is_active,
        "created_at": customer.created_at,
        "id_image_path": customer.id_image_path
    }

# ============  Audit Log ============
@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    user = user_data["user"]
    if user.role == StaffRole.admin:
        query = db.query(AuditLog)
    else:
        query = db.query(AuditLog).filter(AuditLog.branch_id == user.branch_id)

    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": [{"id": l.id, "action": l.action, "actor_id": l.actor_id, "entity_type": l.entity_type, "entity_id": l.entity_id, "created_at": l.created_at} for l in logs]
    }

    # ============ staff ============
@router.get("/staff")
def list_staff(
    search: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    user = user_data["user"]
    if user.role == StaffRole.admin:
        query = db.query(Staff)
    else:
        query = db.query(Staff).filter(Staff.branch_id == user.branch_id)

    if search:
        query = query.filter(
            Staff.full_name.ilike(f"%{search}%") |
            Staff.email.ilike(f"%{search}%")
        )

    total = query.count()
    staff = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": [{"id": s.id, "full_name": s.full_name, "email": s.email, "role": s.role, "branch_id": s.branch_id} for s in staff]
    }

@router.put("/staff/{staff_id}/assign")
def assign_staff(
    staff_id: int,
    branch_id: int = Form(...),
    db: Session = Depends(get_db),
    user_data = Depends(require_manager_or_admin)
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found ❌")

    old_branch = staff.branch_id
    staff.branch_id = branch_id

    log = AuditLog(
        action=ActionType.staff_assigned,
        actor_id=user_data["user"].id,
        actor_role=user_data["user"].role,
        entity_type="staff",
        entity_id=staff_id,
        branch_id=branch_id,
        extra_data={"old_branch_id": old_branch, "new_branch_id": branch_id}
    )
    db.add(log)
    db.commit()

    return {"message": "Staff assigned successfully ✅", "staff_id": staff_id, "branch_id": branch_id}




@router.get("/audit-logs/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    user_data = Depends(require_admin)
):
    logs = db.query(AuditLog).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # header
    writer.writerow(["id", "action", "actor_id", "actor_role", "entity_type", "entity_id", "branch_id", "created_at"])

    # data
    for log in logs:
        writer.writerow([
            log.id,
            log.action,
            log.actor_id,
            log.actor_role,
            log.entity_type,
            log.entity_id,
            log.branch_id,
            log.created_at
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )


    
    

@router.post("/settings/retention")
def set_retention_period(
    days: int = Form(...),
    db: Session = Depends(get_db),
    user_data = Depends(require_admin)
):
    # Save the setting in the database
    db.execute(text(f"CREATE TABLE IF NOT EXISTS settings (key VARCHAR PRIMARY KEY, value VARCHAR)"))
    db.execute(text(f"INSERT INTO settings (key, value) VALUES ('retention_days', '{days}') ON CONFLICT (key) DO UPDATE SET value = '{days}'"))
    db.commit()

    return {"message": f"Retention period set to {days} days ✅"}





# ============ File Retrieval ============
@router.get("/customers/{customer_id}/id-image")
def get_customer_id_image(
    customer_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(require_admin)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found ❌")
    if not customer.id_image_path or not os.path.exists(customer.id_image_path):
        raise HTTPException(status_code=404, detail="Image not found ❌")

    return FileResponse(
        path=customer.id_image_path,
        media_type="image/jpeg",
        filename=f"customer_{customer_id}_id.jpg"
    )

@router.get("/appointments/{appointment_id}/attachment")
def get_appointment_attachment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(get_authenticated_user)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")

    # Customer can only view their own attachment
    if user_data["type"] == "customer":
        if appointment.customer_id != user_data["user"].id:
            raise HTTPException(status_code=403, detail="Access denied 🚫")
    
    if not appointment.attachment_path or not os.path.exists(appointment.attachment_path):
        raise HTTPException(status_code=404, detail="Attachment not found ❌")

    # Detect file type
    ext = appointment.attachment_path.split(".")[-1].lower()
    media_type = "application/pdf" if ext == "pdf" else "image/jpeg"

    return FileResponse(
        path=appointment.attachment_path,
        media_type=media_type,
        filename=f"appointment_{appointment_id}_attachment.{ext}"
    )