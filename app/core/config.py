from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:33445599@localhost:5432/flowcare"
    SECRET_KEY: str = "your-secret-key-change-this"
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB

settings = Settings()