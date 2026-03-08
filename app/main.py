from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app import models
from app.routers import auth, public, appointments
from app.core.init_data import create_default_admin
from app.core.seed import seed_data
# إنشاء الجداول
Base.metadata.create_all(bind=engine)

# إنشاء الأدمن الافتراضي
db = SessionLocal()
create_default_admin(db)
seed_data(db)
db.close()

app = FastAPI(
    title="FlowCare API",
    description="Queue & Appointment Booking System",
    version="1.0.0"
)

# إضافة الـ routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(appointments.router)

@app.get("/")
def root():
    return {"message": "Welcome to FlowCare API 🏥"}