"""
Модель: Услуга в заказе (связь многие-ко-многим)
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text


class OrderService(SQLModel, table=True):
    __tablename__ = "order_services"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True, description="Заказ")
    service_id: int = Field(foreign_key="services.id", description="Услуга")
    service_name: str = Field(max_length=200, description="Название на момент заказа")
    price_at_order: float = Field(default=0, description="Цена на момент заказа")
    quantity: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=datetime.now)
    comment: Optional[str] = Field(default=None, sa_column=Column(Text))

    order: Optional["Order"] = Relationship(back_populates="service_items")
    service: Optional["Service"] = Relationship()

    def __repr__(self):
        return f"<OrderService #{self.id} order={self.order_id} service={self.service_name} {self.price_at_order}₽>"
