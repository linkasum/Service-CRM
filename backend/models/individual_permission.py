"""
Модель: Индивидуальное разрешение для сотрудника
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class IndividualPermission(SQLModel, table=True):
    __tablename__ = "individual_permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, description="ID сотрудника")
    permission: str = Field(max_length=200, description="Разрешение")

    def __repr__(self):
        return f"<IndividualPermission user={self.user_id}:{self.permission}>"
