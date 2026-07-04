from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class NotificationLog(SQLModel, table=True):
    __tablename__ = "notification_logs"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None, max_length=100)
    event_type: str = Field(max_length=50, index=True)
    message: str = Field(max_length=500)
    order_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
