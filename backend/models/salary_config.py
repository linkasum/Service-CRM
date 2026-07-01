"""
Модель: Конфигурация зарплаты (формула или фиксированная)
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Enum as SAEnum
import enum


class SalaryType(str, enum.Enum):
    formula = "formula"      # Процент от работ
    fixed = "fixed"          # Фиксированная сумма


class SalaryPeriod(str, enum.Enum):
    per_order = "per_order"    # За каждый заказ
    per_shift = "per_shift"    # За смену
    per_month = "per_month"    # В месяц


class SalaryConfig(SQLModel, table=True):
    __tablename__ = "salary_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="", max_length=100, description="Название")
    
    config_type: SalaryType = Field(
        default=SalaryType.formula,
        sa_column=Column(SAEnum(SalaryType, name="salary_type")),
        description="Тип: formula или fixed"
    )
    formula_string: Optional[str] = Field(default=None, sa_column=Column(Text), description="Формула для типа formula")
    fixed_amount: Optional[float] = Field(default=None, ge=0, description="Фиксированная сумма для типа fixed")
    
    period: SalaryPeriod = Field(
        default=SalaryPeriod.per_order,
        sa_column=Column(SAEnum(SalaryPeriod, name="salary_period")),
        description="Период: за заказ, за смену, в месяц"
    )
    
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        if self.config_type == SalaryType.fixed:
            return f"<SalaryConfig {self.name} {self.fixed_amount}₽/{self.period}>"
        return f"<SalaryConfig {self.name} {self.formula_string}>"
