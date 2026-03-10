from app.models.staff import Staff, StaffRole
from app.core.security import hash_password

def create_default_admin(db):
    # check if admin is available 
    existing = db.query(Staff).filter(Staff.email == "admin@flowcare.com").first()
    if existing:
        return
    
    admin = Staff(
        full_name="System Admin",
        email="admin@flowcare.com",
        hashed_password=hash_password("admin123"),
        role=StaffRole.admin,
        branch_id=None
    )
    db.add(admin)
    db.commit()
    print("✅ Default admin created: admin@flowcare.com / admin123")