from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routers import auth

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FlowCare API",
    description="Queue & Appointment Booking System",
    version="1.0.0"
)

# إضافة الـ routers
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to FlowCare API 🏥"}

from app.core.init_data import create_default_admin
from app.database import SessionLocal

# إنشاء الأدمن الافتراضي
db = SessionLocal()
create_default_admin(db)
db.close()