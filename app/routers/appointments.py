from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.slot import Slot
from app.core.dependencies import get_authenticated_user, require_customer
from app.core.config import settings
import os
import uuid

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/book")
async def book_appointment(
    slot_id: int = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]

    # تحقق إن السلوت موجود ومتاح
    slot = db.query(Slot).filter(
        Slot.id == slot_id,
        Slot.is_available == True,
        Slot.deleted_at == None
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not available ❌")

    # حفظ المرفق لو موجود
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

    # إنشاء الموعد
    appointment = Appointment(
        slot_id=slot_id,
        customer_id=customer.id,
        attachment_path=attachment_path
    )
    db.add(appointment)

    # تحديث السلوت لغير متاح
    slot.is_available = False
    db.commit()
    db.refresh(appointment)

    return {
        "message": "Appointment booked successfully 📅",
        "appointment_id": appointment.id,
        "slot_id": slot_id,
        "status": appointment.status
    }

@router.get("/my")
def my_appointments(
    db: Session = Depends(get_db),
    user_data = Depends(require_customer)
):
    customer = user_data["user"]
    appointments = db.query(Appointment).filter(
        Appointment.customer_id == customer.id
    ).all()
    return [
        {
            "id": a.id,
            "slot_id": a.slot_id,
            "status": a.status,
            "notes": a.notes,
            "created_at": a.created_at
        } for a in appointments
    ]

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

    # إرجاع السلوت متاح
    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    if slot:
        slot.is_available = True

    appointment.status = AppointmentStatus.cancelled
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

    # تحقق من السلوت الجديد
    new_slot = db.query(Slot).filter(
        Slot.id == new_slot_id,
        Slot.is_available == True,
        Slot.deleted_at == None
    ).first()
    if not new_slot:
        raise HTTPException(status_code=404, detail="New slot not available ❌")

    # إرجاع السلوت القديم متاح
    old_slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    if old_slot:
        old_slot.is_available = True

    # تحديث الموعد
    appointment.slot_id = new_slot_id
    new_slot.is_available = False
    db.commit()

    return {"message": "Appointment rescheduled successfully 📅", "new_slot_id": new_slot_id}