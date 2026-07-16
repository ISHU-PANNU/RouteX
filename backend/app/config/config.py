import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RouteX - Smart Courier & Logistics Platform"
    ENV: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "9e8c4d2b1f8a7e3d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database connection parameters
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "root"
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "routex"
    
    # Combined database connection string
    DATABASE_URL: Optional[str] = None

    GOOGLE_MAPS_API_KEY: Optional[str] = None

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True

    def get_db_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        # Fallback build connection string if MySQL parameters exist
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

settings = Settings()
