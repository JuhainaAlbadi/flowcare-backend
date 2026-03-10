# FlowCare Backend 🏥

Queue & Appointment Booking System for FlowCare service branches across Oman.
Built for **Rihal CodeStacker 2026 - Backend Challenge**.

## Tech Stack
- Python 3.11 + FastAPI
- PostgreSQL + SQLAlchemy + Alembic
- Docker + Docker Compose
- Basic Authentication + Role-Based Access Control

## Features
- ✅ Customer registration with ID image upload
- ✅ Appointment booking, cancellation, and rescheduling
- ✅ Role-based access (Admin, Branch Manager, Staff, Customer)
- ✅ Slot management with Soft Delete
- ✅ Audit logging for all sensitive actions
- ✅ Auto-seeded database on startup
- ✅ Docker support

## Project Structure
flowcare-backend/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── core/
└── uploads/

## Setup Instructions

### 1. Clone the repository
git clone https://github.com/JuhainaAlbadi/flowcare-backend.git
cd flowcare-backend

### 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Setup environment variables
Copy .env.example to .env and update the values:
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/flowcare
SECRET_KEY=your-secret-key

### 5. Run migrations
alembic upgrade head

### 6. Run the server
uvicorn app.main:app --reload

## Run with Docker
docker-compose up --build

## Default Users
| Role | Email | Password |
|------|-------|----------|
| Admin | admin@flowcare.com | admin123 |
| Manager | manager1@flowcare.com | manager123 |
| Staff | staff1@flowcare.com | staff123 |

## API Documentation
After running the server, visit:
http://127.0.0.1:8000/docs

## Example API Usage

### Register Customer
curl -X POST http://127.0.0.1:8000/auth/register \
  -F "full_name=John" \
  -F "email=john@example.com" \
  -F "password=123456" \
  -F "id_image=@image.jpg"

### Login
curl -X POST http://127.0.0.1:8000/auth/login \
  -u "admin@flowcare.com:admin123"

### List Branches
curl http://127.0.0.1:8000/public/branches

### Book Appointment
curl -X POST http://127.0.0.1:8000/appointments/book \
  -u "customer@example.com:password" \
  -F "slot_id=1"
