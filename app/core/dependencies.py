from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user
from app.models.staff import StaffRole

security = HTTPBasic()

def get_authenticated_user(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    user_data = get_current_user(credentials, db)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials ❌")
    return user_data

def require_admin(user_data = Depends(get_authenticated_user)):
    user = user_data["user"]
    if user_data["type"] != "staff" or user.role != StaffRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required 🚫")
    return user_data

def require_manager_or_admin(user_data = Depends(get_authenticated_user)):
    user = user_data["user"]
    if user_data["type"] != "staff" or user.role not in [StaffRole.admin, StaffRole.branch_manager]:
        raise HTTPException(status_code=403, detail="Manager or Admin access required 🚫")
    return user_data

def require_staff_or_above(user_data = Depends(get_authenticated_user)):
    if user_data["type"] != "staff":
        raise HTTPException(status_code=403, detail="Staff access required 🚫")
    return user_data

def require_customer(user_data = Depends(get_authenticated_user)):
    if user_data["type"] != "customer":
        raise HTTPException(status_code=403, detail="Customer access required 🚫")
    return user_data

from datetime import datetime, date
from collections import defaultdict

# In-memory rate limit storage
booking_counts = defaultdict(lambda: {"count": 0, "date": date.today()})

def check_booking_rate_limit(user_data = Depends(get_authenticated_user)):
    user = user_data["user"]
    user_key = f"customer_{user.id}"
    
    today = date.today()
    
    # Reset count if new day
    if booking_counts[user_key]["date"] != today:
        booking_counts[user_key] = {"count": 0, "date": today}
    
    # Check limit (5 bookings per day)
    if booking_counts[user_key]["count"] >= 5:
        raise HTTPException(
            status_code=429,
            detail="Booking limit reached. Maximum 5 bookings per day ❌"
        )
    
    booking_counts[user_key]["count"] += 1
    return user_data