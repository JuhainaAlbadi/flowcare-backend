from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.slot import Slot
from app.core.dependencies import get_authenticated_user, require_customer, check_booking_rate_limit
from app.core.config import settings
import os
import uuid
from app.models.audit_log import AuditLog, ActionType


router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/book")
async def book_appointment(
    slot_id: int = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_data = Depends(check_booking_rate_limit)
):
    customer = user_data["user"]

    # Check if slot exists and is available
    slot = db.query(Slot).filter(
        Slot.id == slot_id,
        Slot.is_available == True,
        Slot.deleted_at == None
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not available ❌")

    # Save attachment if provided
    attachment_path = None
    if attachment and attachment.filename:
        if attachment.content_type not in ["image/jpeg", "image/png", "image/jpg", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Only images and PDF allowed ❌")
        contents = await attachment.read()
        if len(contents) > settings.MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large, max 5MB ❌")
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_ext = attachment.filename.split(".")[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        attachment_path = os.path.join(settings.UPLOAD_DIR, file_name)
        with open(attachment_path, "wb") as f:
            f.write(contents)

    # Create the appointment
    appointment = Appointment(
        slot_id=slot_id,
        customer_id=customer.id,
        attachment_path=attachment_path
    )
    db.add(appointment)

 # Mark slot as unavailable
    slot.is_available = False
    db.commit()
    db.refresh(appointment)

    # Log appointment creation
    log = AuditLog(
        action=ActionType.appointment_created,
        actor_id=customer.id,
        actor_role="customer",
        entity_type="appointment",
        entity_id=appointment.id,
        branch_id=slot.branch_id
    )
    db.add(log)
    db.commit()

    return {
        "message": "Appointment booked successfully 📅",
        "appointment_id": appointment.id,
        "slot_id": slot_id,
        "status": appointment.status
    }

@router.get("/my")
def my_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]
    query = db.query(Appointment).filter(
        Appointment.customer_id == customer.id
    )

    total = query.count()
    appointments = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "results": [
            {
                "id": a.id,
                "slot_id": a.slot_id,
                "status": a.status,
                "notes": a.notes,
                "created_at": a.created_at
            } for a in appointments
        ]
    }

@router.get("/my/{appointment_id}")
def get_appointment_details(
    appointment_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.customer_id == customer.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")

    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()

    return {
        "id": appointment.id,
        "status": appointment.status,
        "notes": appointment.notes,
        "created_at": appointment.created_at,
        "updated_at": appointment.updated_at,
        "attachment_path": appointment.attachment_path,
        "slot": {
            "id": slot.id,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "branch_id": slot.branch_id,
            "service_type_id": slot.service_type_id
        } if slot else None
    }

@router.delete("/cancel/{appointment_id}")
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.customer_id == customer.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Appointment already cancelled ❌")

    # Free up the slot
    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    if slot:
        slot.is_available = True

    appointment.status = AppointmentStatus.cancelled
    # Log appointment cancellation
    log = AuditLog(
        action=ActionType.appointment_cancelled,
        actor_id=customer.id,
        actor_role="customer",
        entity_type="appointment",
        entity_id=appointment_id,
        branch_id=None
    )
    db.add(log)
    db.commit()

    return {"message": "Appointment cancelled successfully ✅"}

@router.put("/reschedule/{appointment_id}")
def reschedule_appointment(
    appointment_id: int,
    new_slot_id: int = Form(...),
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.customer_id == customer.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Cannot reschedule cancelled appointment ❌")

    # Check the new slot
    new_slot = db.query(Slot).filter(
        Slot.id == new_slot_id,
        Slot.is_available == True,
        Slot.deleted_at == None
    ).first()
    if not new_slot:
        raise HTTPException(status_code=404, detail="New slot not available ❌")

    # Free up the old slot
    old_slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    if old_slot:
        old_slot.is_available = True

    # Update the appointment
    appointment.slot_id = new_slot_id
    new_slot.is_available = False
    # Log appointment reschedule
    log = AuditLog(
        action=ActionType.appointment_rescheduled,
        actor_id=customer.id,
        actor_role="customer",
        entity_type="appointment",
        entity_id=appointment_id,
        branch_id=None
    )
    db.add(log)
    db.commit()

    return {"message": "Appointment rescheduled successfully 📅", "new_slot_id": new_slot_id}