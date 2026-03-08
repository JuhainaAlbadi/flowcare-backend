from app.models.branch import Branch
from app.models.service_type import ServiceType
from app.models.staff import Staff, StaffRole
from app.models.slot import Slot
from app.core.security import hash_password
from datetime import datetime, timedelta, timezone

def seed_data(db):
    # تحقق إن البيانات ما موجودة
    if db.query(Branch).first():
        return

    # إنشاء الفروع
    branch1 = Branch(name="Muscat Branch", location="Muscat, Oman", phone="24000001")
    branch2 = Branch(name="Salalah Branch", location="Salalah, Oman", phone="23000001")
    db.add_all([branch1, branch2])
    db.commit()
    db.refresh(branch1)
    db.refresh(branch2)

    # إنشاء الخدمات
    services = [
        ServiceType(name="Medical Checkup", description="General medical checkup", duration_minutes=30, branch_id=branch1.id),
        ServiceType(name="Visa Services", description="Visa application processing", duration_minutes=20, branch_id=branch1.id),
        ServiceType(name="ID Renewal", description="National ID renewal", duration_minutes=15, branch_id=branch1.id),
        ServiceType(name="Medical Checkup", description="General medical checkup", duration_minutes=30, branch_id=branch2.id),
        ServiceType(name="Passport Services", description="Passport processing", duration_minutes=25, branch_id=branch2.id),
        ServiceType(name="License Renewal", description="Driver license renewal", duration_minutes=20, branch_id=branch2.id),
    ]
    db.add_all(services)
    db.commit()

    # إنشاء المدراء والموظفين
    staff_list = [
        Staff(full_name="Ahmed Al-Balushi", email="manager1@flowcare.com", hashed_password=hash_password("manager123"), role=StaffRole.branch_manager, branch_id=branch1.id),
        Staff(full_name="Fatima Al-Rashdi", email="manager2@flowcare.com", hashed_password=hash_password("manager123"), role=StaffRole.branch_manager, branch_id=branch2.id),
        Staff(full_name="Khalid Al-Habsi", email="staff1@flowcare.com", hashed_password=hash_password("staff123"), role=StaffRole.staff, branch_id=branch1.id),
        Staff(full_name="Maryam Al-Hinai", email="staff2@flowcare.com", hashed_password=hash_password("staff123"), role=StaffRole.staff, branch_id=branch1.id),
        Staff(full_name="Omar Al-Farsi", email="staff3@flowcare.com", hashed_password=hash_password("staff123"), role=StaffRole.staff, branch_id=branch2.id),
        Staff(full_name="Noura Al-Zadjali", email="staff4@flowcare.com", hashed_password=hash_password("staff123"), role=StaffRole.staff, branch_id=branch2.id),
    ]
    db.add_all(staff_list)
    db.commit()

    # إنشاء السلوتات للأيام القادمة
    slots = []
    for day in range(1, 8):
        for hour in range(8, 16):
            slot_date = datetime.now(timezone.utc) + timedelta(days=day)
            slot_date = slot_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slots.append(Slot(
                start_time=slot_date,
                end_time=slot_date + timedelta(minutes=30),
                branch_id=branch1.id,
                service_type_id=services[0].id
            ))
            slots.append(Slot(
                start_time=slot_date,
                end_time=slot_date + timedelta(minutes=20),
                branch_id=branch2.id,
                service_type_id=services[3].id
            ))
    db.add