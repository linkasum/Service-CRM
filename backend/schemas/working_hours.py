"""
Схемы для настроек рабочего времени
"""
from typing import Optional
from pydantic import BaseModel, Field


class WorkingHoursCreate(BaseModel):
    day_of_week: int = Field(1, ge=1, le=7)
    day_name: str = Field(..., max_length=20)
    is_working_day: bool = True
    start_time: str = Field("10:00", max_length=5)
    end_time: str = Field("20:00", max_length=5)
    lunch_start: Optional[str] = Field(None, max_length=5)
    lunch_end: Optional[str] = Field(None, max_length=5)
    description: Optional[str] = Field(None, max_length=200)


class WorkingHoursUpdate(BaseModel):
    day_name: Optional[str] = Field(None, max_length=20)
    is_working_day: Optional[bool] = None
    start_time: Optional[str] = Field(None, max_length=5)
    end_time: Optional[str] = Field(None, max_length=5)
    lunch_start: Optional[str] = Field(None, max_length=5)
    lunch_end: Optional[str] = Field(None, max_length=5)
    description: Optional[str] = Field(None, max_length=200)


class WorkingHoursRead(BaseModel):
    id: int
    day_of_week: int
    day_name: str
    is_working_day: bool
    start_time: str
    end_time: str
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    description: Optional[str] = None
    
    class Config:
        from_attributes = True
