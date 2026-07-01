"""
Модель: Настройки компании (реквизиты)
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class CompanySettings(SQLModel, table=True):
    __tablename__ = "company_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    company_name: str = Field(default="Сервисный центр", max_length=300)
    address: Optional[str] = Field(default=None, max_length=500)
    inn: Optional[str] = Field(default=None, max_length=12)
    kpp: Optional[str] = Field(default=None, max_length=9)
    director: Optional[str] = Field(default=None, max_length=200)
    bank: Optional[str] = Field(default=None, max_length=200)
    account: Optional[str] = Field(default=None, max_length=20)
    bik: Optional[str] = Field(default=None, max_length=9)
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=200)
    logo_path: Optional[str] = Field(default=None, max_length=500)
    review_link: Optional[str] = Field(default=None, max_length=500)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<CompanySettings {self.company_name}>"
