"""
Модель: Группа разрешений
"""
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class PermissionGroup(SQLModel, table=True):
    __tablename__ = "permission_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True, description="Название группы: Заказы, Запчасти...")
    description: Optional[str] = Field(default=None, max_length=500)
    permissions: list = Field(
        default_factory=list,
        sa_column=Column(JSON, default=list),
        description="Список разрешений в этой группе"
    )

    def __repr__(self):
        return f"<PermissionGroup {self.name}>"
