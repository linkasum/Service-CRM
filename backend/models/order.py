"""
Модель: Заказ (ремонт)
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text


class Order(SQLModel, table=True):
    __tablename__ = "orders"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_number: Optional[str] = Field(default=None, max_length=50, index=True, description="Пользовательский номер заказа для импорта")

    # === Клиент ===
    client_name: str = Field(max_length=300, index=True)
    client_phone: str = Field(max_length=20, index=True)
    client_type: Optional[str] = Field(default="individual", max_length=20)
    client_email: Optional[str] = Field(default=None, max_length=200)
    client_address: Optional[str] = Field(default=None, max_length=500)
    age_group: Optional[str] = Field(default=None, max_length=50)
    
    # === Источник и персонал ===
    source: Optional[str] = Field(default=None, max_length=100)
    order_type: Optional[str] = Field(default=None, max_length=100)
    manager_id: Optional[int] = Field(default=None, foreign_key="users.id")
    manager_name: Optional[str] = Field(default=None, max_length=100)
    
    # === Устройство ===
    device_category: str = Field(default="phone", max_length=100)
    device_brand: str = Field(default="", max_length=100)
    device_model: str = Field(max_length=300)
    device_model_id: Optional[int] = Field(default=None, foreign_key="device_models.id")
    serial_number: Optional[str] = Field(default=None, max_length=100)
    accessories: Optional[str] = Field(default=None, sa_column=Column(Text))
    appearance: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # === Проблема ===
    complaint: str = Field(sa_column=Column(Text))
    
    # === Дополнительно ===
    diagnostics_days: int = Field(default=3)
    is_warranty: bool = Field(default=False)
    has_delivery: bool = Field(default=False)
    comment: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # === Статус и сотрудники ===
    status: str = Field(default="new", max_length=20, index=True)
    master_id: Optional[int] = Field(default=None, foreign_key="users.id")
    acceptor_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    # === Даты ===
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    ready_at: Optional[datetime] = Field(default=None)
    issued_at: Optional[datetime] = Field(default=None)
    
    # === Финансы ===
    total_cost: Optional[float] = Field(default=None, ge=0)
    parts_cost: Optional[float] = Field(default=0, ge=0)
    work_cost: Optional[float] = Field(default=0, ge=0)
    paid_amount: Optional[float] = Field(default=0, ge=0)
    
    # === Диагностика ===
    diagnostic_act_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    
    # === Гарантия ===
    warranty_days: Optional[int] = Field(default=None, ge=0)
    warranty_until: Optional[datetime] = Field(default=None)
    
    # Связи — БЕЗ forward references, просто строки
    master: Optional["User"] = Relationship(
        back_populates="orders_as_master",
        sa_relationship_kwargs={"foreign_keys": "[Order.master_id]"}
    )
    acceptor: Optional["User"] = Relationship(
        back_populates="orders_as_acceptor",
        sa_relationship_kwargs={"foreign_keys": "[Order.acceptor_id]"}
    )
    parts: List["OrderPart"] = Relationship(back_populates="order")
    salary_records: List["SalaryRecord"] = Relationship(back_populates="order")
    notification_tasks: List["NotificationTask"] = Relationship(back_populates="order")
    payments: List["OrderPayment"] = Relationship(back_populates="order")
    service_items: List["OrderService"] = Relationship(back_populates="order")
    model: Optional["DeviceModel"] = Relationship(back_populates="orders")

    def __repr__(self):
        return f"<Order #{self.id} {self.client_name}>"
