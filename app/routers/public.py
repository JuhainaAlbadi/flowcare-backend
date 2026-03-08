from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.branch import Branch
from app.models.service_type import ServiceType
from app.models.slot import Slot
from datetime import datetime

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/branches")
def list_branches(db: Session = Depends(get_db)):
    branches = db.query(Branch).filter(Branch.is_active == True).all()
    return [{"id": b.id, "name": b.name, "location": b.location, "phone": b.phone} for b in branches]

@router.get("/branches/{branch_id}/services")
def list_services(branch_id: int, db: Session = Depends(get_db)):
    services = db.query(ServiceType).filter(
        ServiceType.branch_id == branch_id,
        ServiceType.is_active == True
    ).all()
    return [{"id": s.id, "name": s.name, "description": s.description, "duration_minutes": s.duration_minutes} for s in services]

@router.get("/branches/{branch_id}/slots")
def list_available_slots(
    branch_id: int,
    service_type_id: int = Query(None),
    date: str = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Slot).filter(
        Slot.branch_id == branch_id,
        Slot.is_available == True,
        Slot.deleted_at == None
    )
    if service_type_id:
        query = query.filter(Slot.service_type_id == service_type_id)
    if date:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        query = query.filter(Slot.start_time >= date_obj)
    slots = query.all()
    return [{"id": s.id, "start_time": s.start_time, "end_time": s.end_time, "service_type_id": s.service_type_id} for s in slots]