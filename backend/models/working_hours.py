"""
Модель: Настройки рабочего времени компании
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class WorkingHours(SQLModel, table=True):
    __tablename__ = "working_hours"

    id: Optional[int] = Field(default=None, primary_key=True)
    day_of_week: int = Field(default=1)  # 1=Понедельник, 7=Воскресенье
    day_name: str = Field(default="Понедельник", max_length=20)
    is_working_day: bool = Field(default=True)
    start_time: str = Field(default="10:00", max_length=5)  # Формат HH:MM
    end_time: str = Field(default="20:00", max_length=5)  # Формат HH:MM
    lunch_start: Optional[str] = Field(default=None, max_length=5)  # Обед начало
    lunch_end: Optional[str] = Field(default=None, max_length=5)  # Обед конец
    description: Optional[str] = Field(default=None, max_length=200)

    def __repr__(self):
        return f"<WorkingHours {self.day_name} {self.start_time}-{self.end_time}>"
