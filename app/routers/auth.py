from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.customer import Customer
from app.core.security import hash_password
from app.core.config import settings
import shutil
import os
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register_customer(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(None),
    id_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # تحقق إن الإيميل ما يتكرر
    existing = db.query(Customer).filter(Customer.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # تحقق من نوع الصورة
    if id_image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only images are allowed")

    # تحقق من حجم الصورة
    contents = await id_image.read()
    if len(contents) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large, max 5MB")

    # حفظ الصورة
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_ext = id_image.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_name)

    with open(file_path, "wb") as f:
        f.write(contents)

    # إنشاء الزبون
    customer = Customer(
        full_name=full_name,
        email=email,
        phone=phone,
        hashed_password=hash_password(password),
        id_image_path=file_path
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)

    return {"message": "Customer registered successfully ✅", "id": customer.id}



from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@router.post("/login")
def login(
    credentials: HTTPBasicCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    from app.core.security import get_current_user
    user_data = get_current_user(credentials, db)
    
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password ❌"
        )
    
    user = user_data["user"]
    user_type = user_data["type"]
    
    return {
        "message": "Login successful ✅",
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "type": user_type
    }