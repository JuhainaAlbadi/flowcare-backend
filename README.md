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


## Database Schema

### branches
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| name | String | Branch name |
| location | String | Branch location |
| phone | String | Branch phone |

### service_types
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| name | String | Service name |
| description | String | Service description |
| duration_minutes | Integer | Duration in minutes |
| branch_id | Integer | FK → branches |

### staff
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| full_name | String | Full name |
| email | String | Email (unique) |
| hashed_password | String | Hashed password |
| role | Enum | admin, branch_manager, staff |
| is_active | Boolean | Account status |
| branch_id | Integer | FK → branches (nullable) |
| created_at | DateTime | Creation date |

### customers
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| full_name | String | Full name |
| email | String | Email (unique) |
| hashed_password | String | Hashed password |
| phone | String | Phone number |
| id_image_path | String | Path to ID image |
| is_active | Boolean | Account status |
| created_at | DateTime | Registration date |

### slots
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| branch_id | Integer | FK → branches |
| service_type_id | Integer | FK → service_types |
| staff_id | Integer | FK → staff (nullable) |
| start_time | DateTime | Slot start time |
| end_time | DateTime | Slot end time |
| is_available | Boolean | Availability status |
| created_at | DateTime | Creation date |
| deleted_at | DateTime | Soft delete timestamp (nullable) |

### appointments
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| customer_id | Integer | FK → customers |
| slot_id | Integer | FK → slots |
| staff_id | Integer | FK → staff (nullable) |
| status | Enum | booked, checked_in, completed, no_show, cancelled |
| notes | String | Optional notes (nullable) |
| attachment_path | String | Path to attachment (nullable) |
| created_at | DateTime | Booking date |
| updated_at | DateTime | Last update date |

### audit_logs
| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary Key |
| action | Enum | Action type |
| actor_id | Integer | User who performed action |
| actor_role | String | Role of actor |
| entity_type | String | Type of entity |
| entity_id | Integer | ID of entity |
| branch_id | Integer | FK → branches (nullable) |
| extra_data | JSON | Additional metadata |
| created_at | DateTime | Log timestamp |

### settings
| Column | Type | Description |
|--------|------|-------------|
| key | String | Primary Key |
| value | String | Setting value |


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

The database is automatically seeded on startup using `seed_data.json` with:
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

Cancel appointment:

    curl -X DELETE http://127.0.0.1:8000/appointments/cancel/1 \
      -u "customer@example.com:password"

Reschedule appointment:

    curl -X PUT http://127.0.0.1:8000/appointments/reschedule/1 \
      -u "customer@example.com:password" \
      -F "new_slot_id=2"

Create bulk slots:

    curl -X POST http://127.0.0.1:8000/admin/slots \
      -u "admin@flowcare.com:admin123" \
      -F "branch_id=1" \
      -F "service_type_id=1" \
      -F "start_times=2026-03-20T08:00:00,2026-03-20T09:00:00" \
      -F "end_times=2026-03-20T08:30:00,2026-03-20T09:30:00"

Get queue position:

    curl http://127.0.0.1:8000/queue/position/1 \
      -u "customer@example.com:password"

Export audit logs:

    curl http://127.0.0.1:8000/admin/audit-logs/export \
      -u "admin@flowcare.com:admin123"