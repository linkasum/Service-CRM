"""
Модель: График работы сотрудников
"""
from typing import Optional
from datetime import date as date_type, datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint, Column, Date


class WorkSchedule(SQLModel, table=True):
    __tablename__ = 'work_schedules'
    __table_args__ = (
        UniqueConstraint('user_id', 'date', name='uq_work_schedules_user_date'),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='users.id', index=True)
    date: Optional[date_type] = Field(default=None, sa_column=Column(Date, index=True, nullable=False))
    created_by: Optional[int] = Field(default=None, foreign_key='users.id')
    created_at: datetime = Field(default_factory=datetime.utcnow)
