"""
Модель: Кассовая смена
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class CashShift(SQLModel, table=True):
    __tablename__ = "cash_shifts"

    id: Optional[int] = Field(default=None, primary_key=True)
    opened_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    closed_at: Optional[datetime] = Field(default=None)
    opened_by: int = Field(foreign_key="users.id", index=True)
    closed_by: Optional[int] = Field(default=None)
    initial_amount: float = Field(default=0, ge=0)
    final_amount: float = Field(default=0, ge=0)
    is_open: bool = Field(default=True)

    # Relationships
    transactions: List["CashTransaction"] = Relationship(back_populates="shift")

    def __repr__(self):
        return f"<CashShift #{self.id} {'open' if self.is_open else 'closed'}>"
