"""
Модель: Возрастная группа клиента
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class AgeGroup(SQLModel, table=True):
    __tablename__ = "age_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    is_active: bool = Field(default=True)

    def __repr__(self):
        return f"<AgeGroup {self.name}>"
