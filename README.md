# Rihal Challenge 2026 - flowcare backend


# FlowCare Backend 🏥

Queue & Appointment Booking System for FlowCare branches across Oman.

## Project Structure
```
flowcare-backend/
│
├── app/
│   ├── main.py          # Entry point
│   ├── database.py      # Database connection
│   ├── models/          # Database tables
│   ├── routers/         # API endpoints
│   ├── schemas/         # Request/Response shapes
│   └── core/
│       ├── config.py    # App settings
│       └── security.py  # Auth & permissions
│
└── uploads/             # ID images & attachments
```

## Tech Stack
- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
