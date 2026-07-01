"""
Конфигурация приложения
"""
import os
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache

# Загружаем .env вручную
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_env_path, override=True)


class Settings(BaseSettings):
    """Настройки приложения"""
    
    DATABASE_URL: str = Field(default=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/qwencrm"))
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", "your-secret-key-change-in-production"))
    ALGORITHM: str = Field(default=os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")))
    TELEGRAM_BOT_TOKEN: str = Field(default=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    SMS_API_KEY: str = Field(default=os.getenv("SMS_API_KEY", ""))
    SMS_SERVICE_ENABLED: bool = Field(default=os.getenv("SMS_SERVICE_ENABLED", "false").lower() == "true")
    COMPANY_NAME: str = Field(default=os.getenv("COMPANY_NAME", "Сервисный центр"))
    COMPANY_INN: str = Field(default=os.getenv("COMPANY_INN", ""))
    COMPANY_ADDRESS: str = Field(default=os.getenv("COMPANY_ADDRESS", ""))
    COMPANY_PHONE: str = Field(default=os.getenv("COMPANY_PHONE", ""))
    LOG_LEVEL: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))


@lru_cache()
def get_settings() -> Settings:
    """Получить настройки приложения (кэшируется)"""
    return Settings()
