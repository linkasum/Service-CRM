"""
Настройка базы данных
"""
from sqlmodel import SQLModel, create_engine, Session
from core.config import get_settings

# Импорт моделей регистрирует их в SQLModel.metadata
from models.all_models import *  # noqa: F401, F403

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def create_db_and_tables():
    """Создать все таблицы"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Получить сессию базы данных"""
    with Session(engine) as session:
        yield session
