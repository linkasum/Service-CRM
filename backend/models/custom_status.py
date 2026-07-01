"""
Модель: Статус заказа (кастомные статусы)
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class CustomStatus(SQLModel, table=True):
    __tablename__ = "custom_statuses"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    code: Optional[str] = Field(default=None, max_length=50, index=True)  # new, diagnostics, repair и т.д.
    color: str = Field(default="#1890ff", max_length=20)
    is_default: bool = Field(default=False)
    is_active: bool = Field(default=True)

    def __repr__(self):
        return f"<CustomStatus {self.name}>"
