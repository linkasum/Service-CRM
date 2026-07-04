"""
Модель: Платёж по заказу
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text, Enum as SAEnum
import enum


class PaymentType(str, enum.Enum):
    prepayment = "prepayment"       # Предоплата
    final = "final"                  # Окончательный расчёт
    refund = "refund"                # Возврат предоплаты
    expense = "expense"              # Служебный расход


class PaymentStatus(str, enum.Enum):
    pending = "pending"              # Ожидает
    completed = "completed"          # Проведён
    cancelled = "cancelled"          # Отменён


class PaymentMethod(str, enum.Enum):
    cash = "cash"                    # Наличные
    card = "card"                    # Карта
    transfer = "transfer"            # Перевод


class OrderPayment(SQLModel, table=True):
    __tablename__ = "order_payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True, description="Заказ")
    
    payment_type: PaymentType = Field(
        default=PaymentType.prepayment,
        sa_column=Column(SAEnum(PaymentType, name="payment_type")),
        description="Тип платежа"
    )
    amount: float = Field(description="Сумма")
    method: PaymentMethod = Field(
        default=PaymentMethod.cash,
        sa_column=Column(SAEnum(PaymentMethod, name="payment_method")),
        description="Способ оплаты"
    )
    status: PaymentStatus = Field(
        default=PaymentStatus.completed,
        sa_column=Column(SAEnum(PaymentStatus, name="payment_status")),
        description="Статус"
    )
    comment: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=datetime.now)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id")
    
    # Связи
    order: Optional["Order"] = Relationship(back_populates="payments")

    def __repr__(self):
        return f"<OrderPayment #{self.id} order={self.order_id} {self.payment_type.value} {self.amount}₽>"
