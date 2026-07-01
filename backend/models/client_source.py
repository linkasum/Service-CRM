"""
Модель: Источник клиента
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class ClientSource(SQLModel, table=True):
    __tablename__ = "client_sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=200, unique=True, index=True)
    is_active: bool = Field(default=True)

    def __repr__(self):
        return f"<ClientSource {self.name}>"
