"""
Схемы для Notification и Client
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationTaskBase(BaseModel):
    order_id: int
    client_phone: Optional[str] = None
    chat_id: Optional[int] = None
    message_text: str = Field(..., max_length=2000)
    send_at: datetime


class NotificationTaskCreate(NotificationTaskBase):
    pass


class NotificationTaskRead(NotificationTaskBase):
    id: int
    is_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationUpdate(BaseModel):
    is_sent: bool


class ClientBase(BaseModel):
    name: str
    phone: str


class ClientRead(BaseModel):
    id: int
    name: str
    phone: str
    client_type: Optional[str] = None
    total_orders: int = 0
    last_order_date: Optional[datetime] = None


class ClientListResponse(BaseModel):
    clients: List[ClientRead]
    total: int


class ClientFilter(BaseModel):
    search: Optional[str] = None
    skip: int = 0
    limit: int = 50


class CompanySettingsBase(BaseModel):
    company_name: str = Field(default="Сервисный центр", max_length=300)
    inn: Optional[str] = Field(None, max_length=12)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    logo_path: Optional[str] = None
    review_link: Optional[str] = Field(None, max_length=500)


class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    inn: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_path: Optional[str] = None
    review_link: Optional[str] = None


class CompanySettingsRead(CompanySettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentTemplateBase(BaseModel):
    type: str = Field(..., max_length=50)
    content_template: str


class DocumentTemplateCreate(DocumentTemplateBase):
    pass


class DocumentTemplateUpdate(BaseModel):
    content_template: Optional[str] = None


class DocumentTemplateRead(DocumentTemplateBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
