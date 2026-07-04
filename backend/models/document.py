"""
Модель: Сгенерированный документ заказа
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id", index=True)
    document_type: str = Field(max_length=50, index=True)  # receipt, diagnostic_act, work_act, invoice
    filename: str = Field(max_length=255)
    status: str = Field(default="generated", max_length=30)  # generated, sent, signed, cancelled
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    created_by: Optional[int] = Field(default=None, foreign_key="users.id")
    sent_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=500)

    def __repr__(self):
        return f"<Document #{self.id} order={self.order_id} type={self.document_type}>"
