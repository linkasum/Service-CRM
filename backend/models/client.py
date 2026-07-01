"""
Модель: Клиент
"""

from typing import Optional
from sqlmodel import SQLModel, Field


class Client(SQLModel, table=True):
    __tablename__ = "clients"

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=300, index=True)
    phone: str = Field(max_length=20, index=True)
    client_type: Optional[str] = Field(default="individual", max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    address: Optional[str] = Field(default=None, max_length=500)
    age_group: Optional[str] = Field(default=None, max_length=50)
    source: Optional[str] = Field(default=None, max_length=100)

    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)
