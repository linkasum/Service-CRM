"""
Модель: Связь заказа и запчасти
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class OrderPart(SQLModel, table=True):
    __tablename__ = "order_parts"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    part_id: int = Field(foreign_key="parts.id")
    quantity: int = Field(default=1, gt=0)
    price_at_order: float = Field(default=0, ge=0)
    master_id: Optional[int] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.now)

    order: Optional["Order"] = Relationship(back_populates="parts")
    part: Optional["Part"] = Relationship(back_populates="order_parts")
