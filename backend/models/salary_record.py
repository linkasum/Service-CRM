"""
Модель: Ведомость зарплаты
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class SalaryRecord(SQLModel, table=True):
    __tablename__ = "salary_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    order_id: Optional[int] = Field(default=None, foreign_key="orders.id")
    calculated_amount: float = Field(default=0, ge=0)
    status: str = Field(default="accrued", max_length=20)
    period_start: datetime = Field(index=True)
    period_end: datetime = Field(index=True)
    comment: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship(back_populates="salary_records")
    order: Optional["Order"] = Relationship(back_populates="salary_records")

    def __repr__(self):
        return f"<SalaryRecord #{self.id} user={self.user_id} amount={self.calculated_amount}>"
