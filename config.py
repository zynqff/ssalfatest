from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Параметры базы данных
    DATABASE_URL: str = "sqlite:///./database.db"
    
    # Параметры безопасности (JWT)
    SECRET_KEY: str = "super-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    # ЭТОЙ СТРОКИ НЕ ХВАТАЛО:
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 
    
    # API ключи
    GROQ_API_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()

