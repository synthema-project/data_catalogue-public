import os

class Settings:
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "task_center")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER","user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD","pass")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres_db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432") #5432 80

settings = Settings()
