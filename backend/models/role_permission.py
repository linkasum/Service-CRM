"""
Модель: Привязка разрешения к роли с группой
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class RolePermission(SQLModel, table=True):
    __tablename__ = "role_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    role_name: str = Field(max_length=100, index=True, description="Название роли")
    group_name: Optional[str] = Field(default=None, max_length=100, description="Название группы разрешений")
    permission: str = Field(max_length=200, description="Разрешение в точечной нотации: orders:create")

    def __repr__(self):
        return f"<RolePermission {self.role_name}:{self.permission}>"
