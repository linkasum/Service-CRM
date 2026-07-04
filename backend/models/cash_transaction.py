"""
Модель: Транзакция кассы (приход, расход, корректировка, инкассация)
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Text, Enum as SAEnum
import enum


class TransactionType(str, enum.Enum):
    income = "income"              # Приход (оплата заказа)
    expense = "expense"            # Расход
    adjustment = "adjustment"      # Корректировка
    cashout = "cashout"            # Инкассация (вывод наличных)


class PaymentMethod(str, enum.Enum):
    cash = "cash"                  # Наличные
    card = "card"                  # Безналичные (карта)


class CashTransaction(SQLModel, table=True):
    __tablename__ = "cash_transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    shift_id: int = Field(foreign_key="cash_shifts.id", index=True, description="Кассовая смена")
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id", description="Связанный заказ")

    transaction_type: TransactionType = Field(
        sa_column=Column(SAEnum(TransactionType, name="transaction_type")),
        description="Тип операции"
    )
    payment_method: Optional[PaymentMethod] = Field(
        default=PaymentMethod.cash,
        sa_column=Column(SAEnum(PaymentMethod, name="payment_method", nullable=True)),
        description="Способ оплаты"
    )
    amount: float = Field(description="Сумма (положительная для прихода, отрицательная для расхода)")
    comment: Optional[str] = Field(default=None, sa_column=Column(Text), description="Комментарий")
    
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    created_by: int = Field(foreign_key="users.id", description="Кто провёл операцию")

    shift: Optional["CashShift"] = Relationship(back_populates="transactions")

    def __repr__(self):
        return f"<CashTransaction #{self.id} {self.transaction_type.value} {self.amount}₽>"
