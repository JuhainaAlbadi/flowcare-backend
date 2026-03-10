from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app import models
from app.routers import auth, public, appointments, admin 
from app.core.init_data import create_default_admin
from app.core.seed import seed_data
# Create database tables
Base.metadata.create_all(bind=engine)

# Create default admin
db = SessionLocal()
create_default_admin(db)
seed_data(db)
db.close()

app = FastAPI(
    title="FlowCare API",
    description="Queue & Appointment Booking System",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(public.router)
app.include_router(appointments.router)
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Welcome to FlowCare API 🏥"}