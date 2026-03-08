from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class CustomerRegister(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str

class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True