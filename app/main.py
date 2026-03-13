from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app import models
from app.routers import auth, public, appointments, admin, queue
from app.core.init_data import create_default_admin
from app.core.seed import seed_data
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from app.models.slot import Slot
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog, ActionType
from datetime import datetime, timezone, timedelta

# Create database tables
Base.metadata.create_all(bind=engine)

# Create default admin and seed data
db = SessionLocal()
create_default_admin(db)
seed_data(db)
db.close()

def auto_cleanup():
    db = SessionLocal()
    try:
        # Get retention period
        result = db.execute(text("SELECT value FROM settings WHERE key = 'retention_days'")).fetchone()
        retention_days = int(result[0]) if result else 30

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        old_slots = db.query(Slot).filter(
            Slot.deleted_at != None,
            Slot.deleted_at <= cutoff
        ).all()

        count = 0
        for slot in old_slots:
            # Handle related appointments
            related = db.query(Appointment).filter(
                Appointment.slot_id == slot.id
            ).all()
            for appointment in related:
                appointment.slot_id = None

            log = AuditLog(
                action=ActionType.slot_hard_deleted,
                actor_id=0,
                actor_role="system",
                entity_type="slot",
                entity_id=slot.id,
                branch_id=slot.branch_id
            )
            db.add(log)
            db.delete(slot)
            count += 1

        db.commit()
        if count > 0:
            print(f"✅ Auto cleanup: removed {count} soft-deleted slots")
    except Exception as e:
        print(f"❌ Auto cleanup error: {e}")
    finally:
        db.close()

app = FastAPI(
    title="FlowCare API",
    description="Queue & Appointment Booking System",
    version="1.0.0"
)

# Background scheduler - runs every day at midnight
scheduler = BackgroundScheduler()
scheduler.add_job(auto_cleanup, "cron", hour=0, minute=0)
scheduler.start()

# Include routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(appointments.router)
app.include_router(admin.router)
app.include_router(queue.router)

@app.get("/")
def root():
    return {"message": "Welcome to FlowCare API 🏥"}