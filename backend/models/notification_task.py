"""
Модель: Задача уведомления
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class NotificationTask(SQLModel, table=True):
    __tablename__ = "notification_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    client_phone: Optional[str] = Field(default=None, max_length=20)
    chat_id: Optional[int] = Field(default=None)
    message_text: str = Field(max_length=2000)
    send_at: datetime = Field(index=True)
    is_sent: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    order: Optional["Order"] = Relationship(back_populates="notification_tasks")

    def __repr__(self):
        return f"<NotificationTask #{self.id} send_at={self.send_at}>"
