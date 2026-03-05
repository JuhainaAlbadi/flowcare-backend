from fastapi import FastAPI
from app.database import engine, Base
from app import models

# إنشاء الجداول
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FlowCare API",
    description="Queue & Appointment Booking System",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Welcome to FlowCare API 🏥"}
