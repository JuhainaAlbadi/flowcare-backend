from passlib.context import CryptContext
from app.database import SessionLocal
from app.models.staff import Staff
from app.models.customer import Customer

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_current_user(credentials, db):
    email = credentials.username
    password = credentials.password

    # نشوف أول في Staff
    user = db.query(Staff).filter(Staff.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return {"user": user, "type": "staff"}

    # بعدين في Customer
    user = db.query(Customer).filter(Customer.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return {"user": user, "type": "customer"}

    return None