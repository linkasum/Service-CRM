"""
Схемы для Salary
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SalaryConfigBase(BaseModel):
    formula_string: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=500)


class SalaryConfigCreate(SalaryConfigBase):
    pass


class SalaryConfigUpdate(BaseModel):
    formula_string: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class SalaryConfigRead(SalaryConfigBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SalaryRecordBase(BaseModel):
    user_id: int
    order_id: Optional[int] = None
    calculated_amount: float = Field(default=0, ge=0)
    status: str = Field(default="accrued", max_length=20)
    period_start: datetime
    period_end: datetime
    comment: Optional[str] = Field(None, max_length=500)


class SalaryRecordCreate(SalaryRecordBase):
    pass


class SalaryRecordRead(SalaryRecordBase):
    id: int
    created_at: datetime
    username: Optional[str] = None

    class Config:
        from_attributes = True


class SalaryCalculationPreview(BaseModel):
    """Предпросмотр расчёта зарплаты"""
    order_id: int
    total: float
    parts: float
    work: float
    formula: str
    result: float


class SalaryPeriodRequest(BaseModel):
    """Запрос на формирование ведомости за период"""
    period_start: datetime
    period_end: datetime
    status: str = Field(default="accrued", description="accrued, paid, advance")
