from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus
from app.models.slot import Slot
from app.core.dependencies import get_authenticated_user

router = APIRouter(prefix="/queue", tags=["Queue"])

@router.get("/position/{appointment_id}")
def get_queue_position(
    appointment_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(get_authenticated_user)
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found ❌")

    # Get the slot details
    slot = db.query(Slot).filter(Slot.id == appointment.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found ❌")

    # Count appointments ahead in the same branch with status booked or checked_in
    position = db.query(Appointment).join(Slot).filter(
        Slot.branch_id == slot.branch_id,
        Appointment.status.in_([AppointmentStatus.booked, AppointmentStatus.checked_in]),
        Appointment.id < appointment_id
    ).count()

    # Count total waiting in branch
    total_waiting = db.query(Appointment).join(Slot).filter(
        Slot.branch_id == slot.branch_id,
        Appointment.status.in_([AppointmentStatus.booked, AppointmentStatus.checked_in])
    ).count()

    return {
        "appointment_id": appointment_id,
        "branch_id": slot.branch_id,
        "queue_position": position + 1,
        "total_waiting": total_waiting,
        "status": appointment.status
    }

@router.get("/branch/{branch_id}")
def get_branch_queue(
    branch_id: int,
    db: Session = Depends(get_db),
    user_data = Depends(get_authenticated_user)
):
    appointments = db.query(Appointment).join(Slot).filter(
        Slot.branch_id == branch_id,
        Appointment.status.in_([AppointmentStatus.booked, AppointmentStatus.checked_in])
    ).order_by(Appointment.id).all()

    return {
        "branch_id": branch_id,
        "total_waiting": len(appointments),
        "queue": [
            {
                "position": idx + 1,
                "appointment_id": a.id,
                "status": a.status
            } for idx, a in enumerate(appointments)
        ]
    }