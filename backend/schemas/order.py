"""
Схемы для Order
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OrderBase(BaseModel):
    # Клиент
    client_name: str = Field(..., max_length=300)
    client_phone: str = Field(..., max_length=20)
    client_type: str = Field(default="individual", max_length=20)
    client_email: Optional[str] = Field(None, max_length=200)
    client_address: Optional[str] = Field(None, max_length=500)
    age_group: Optional[str] = Field(None, max_length=50)
    
    # Источник и персонал
    source: Optional[str] = Field(None, max_length=100)
    order_type: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    
    # Устройство
    device_category: str = Field(..., max_length=100)
    device_brand: str = Field(..., max_length=100)
    device_model: str = Field(..., max_length=300)
    serial_number: Optional[str] = Field(None, max_length=100)
    accessories: Optional[str] = Field(None, max_length=1000)
    appearance: Optional[str] = Field(None, max_length=100)
    
    # Проблема
    complaint: str = Field(...)
    
    # Дополнительно
    diagnostics_days: int = Field(default=3)
    is_warranty: bool = Field(default=False)
    has_delivery: bool = Field(default=False)
    comment: Optional[str] = Field(None, max_length=2000)


class OrderCreate(OrderBase):
    # Финансы
    master_id: Optional[int] = None
    acceptor_id: Optional[int] = None
    total_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    work_cost: Optional[float] = None


class OrderUpdate(BaseModel):
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_type: Optional[str] = None
    client_email: Optional[str] = None
    client_address: Optional[str] = None
    age_group: Optional[str] = None
    source: Optional[str] = None
    order_type: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    device_category: Optional[str] = None
    device_brand: Optional[str] = None
    device_model: Optional[str] = None
    serial_number: Optional[str] = None
    accessories: Optional[str] = None
    appearance: Optional[str] = None
    complaint: Optional[str] = None
    diagnostics_days: Optional[int] = None
    is_warranty: Optional[bool] = None
    has_delivery: Optional[bool] = None
    comment: Optional[str] = None
    status: Optional[str] = None
    master_id: Optional[int] = None
    acceptor_id: Optional[int] = None
    ready_at: Optional[datetime] = None
    total_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    work_cost: Optional[float] = None
    paid_amount: Optional[float] = None
    order_number: Optional[str] = None
    diagnostic_act_text: Optional[str] = None
    warranty_days: Optional[int] = None
    issued_at: Optional[datetime] = None
    order_number: Optional[str] = None


class OrderStatusChange(BaseModel):
    status: str = Field(..., description="Новый статус")
    comment: Optional[str] = None
    payment_method: Optional[str] = None


class OrderRead(OrderBase):
    id: int
    order_number: Optional[str] = None
    status: str
    master_id: Optional[int] = None
    master_username: Optional[str] = None
    acceptor_id: Optional[int] = None
    acceptor_username: Optional[str] = None
    created_at: datetime
    ready_at: Optional[datetime] = None
    issued_at: Optional[datetime] = None
    total_cost: Optional[float] = None
    parts_cost: Optional[float] = 0
    work_cost: Optional[float] = 0
    refunds_amount: Optional[float] = 0  # Сумма возвратов
    warranty_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderFilter(BaseModel):
    status: Optional[str] = None
    master_id: Optional[int] = None
    client_phone: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    skip: int = 0
    limit: int = 50
