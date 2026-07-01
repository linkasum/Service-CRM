"""
Модель: Роль пользователя
"""
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, description="Название роли: admin, manager, master, acceptor, courier")
    permissions: list = Field(
        default_factory=list,
        sa_column=Column(JSON, default=list),
        description="Список прав доступа"
    )
    description: Optional[str] = Field(default=None, max_length=500)

    users: List["User"] = Relationship(back_populates="role")

    def __repr__(self):
        return f"<Role {self.name}>"
