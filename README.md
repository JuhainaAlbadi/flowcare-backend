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
- ✅ Slot management with Soft Delete + retention period
- ✅ Audit logging for all sensitive actions with CSV export
- ✅ File retrieval for ID images and appointment attachments
- ✅ Pagination and search support
- ✅ Queue position tracking per branch
- ✅ Rate limiting (max 5 bookings per day per customer)
- ✅ Background scheduling for automatic cleanup
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
    ├── alembic/
    ├── uploads/
    ├── Dockerfile
    └── docker-compose.yml

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

Create a `.env` file:

    DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/flowcare
    SECRET_KEY=your-secret-key
    UPLOAD_DIR=uploads
    MAX_FILE_SIZE=5242880

### 5. Create database

Create a database named `flowcare` in PostgreSQL.

### 6. Run migrations

    alembic upgrade head

### 7. Run the server

    uvicorn app.main:app --reload

## Run with Docker

    docker-compose up --build

## Default Users

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@flowcare.com | admin123 |
| Manager (Muscat) | manager1@flowcare.com | manager123 |
| Manager (Salalah) | manager2@flowcare.com | manager123 |
| Staff (Muscat) | staff1@flowcare.com | staff123 |
| Staff (Muscat) | staff2@flowcare.com | staff123 |
| Staff (Salalah) | staff3@flowcare.com | staff123 |
| Staff (Salalah) | staff4@flowcare.com | staff123 |

## Seed Data

The database is automatically seeded on startup with:
- 2 branches (Muscat, Salalah)
- 3 service types per branch
- 1 manager + 2 staff per branch
- Slots for the next 7 days

Seeding is idempotent — running the app multiple times will not duplicate data.

## API Documentation

After running the server, visit: http://127.0.0.1:8000/docs

## Example API Usage

List branches (public):

    curl http://127.0.0.1:8000/public/branches

Register customer:

    curl -X POST http://127.0.0.1:8000/auth/register \
      -F "full_name=John" \
      -F "email=john@example.com" \
      -F "password=123456" \
      -F "id_image=@image.jpg"

Login:

    curl -X POST http://127.0.0.1:8000/auth/login \
      -u "admin@flowcare.com:admin123"

Book appointment:

    curl -X POST http://127.0.0.1:8000/appointments/book \
      -u "customer@example.com:password" \
      -F "slot_id=1"

Get queue position:

    curl http://127.0.0.1:8000/queue/position/1 \
      -u "customer@example.com:password"