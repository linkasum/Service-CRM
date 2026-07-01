"""
Модель: Услуга
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text, Enum as SAEnum
import enum


class ServiceStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class Service(SQLModel, table=True):
    __tablename__ = "services"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, description="Название услуги")
    description: Optional[str] = Field(default=None, sa_column=Column(Text), description="Описание")
    price: float = Field(default=0, ge=0, description="Цена")
    status: ServiceStatus = Field(
        default=ServiceStatus.active,
        sa_column=Column(SAEnum(ServiceStatus, name="service_status")),
        description="Статус"
    )
    duration_minutes: Optional[int] = Field(default=None, ge=0, description="Время выполнения (мин)")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<Service #{self.id} {self.name} {self.price}₽>"
