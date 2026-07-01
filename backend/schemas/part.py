"""
Схемы для Part (запчасти)
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PartBase(BaseModel):
    name: str = Field(..., max_length=300)
    article: str = Field(..., max_length=100)
    quantity: int = Field(default=0, ge=0)
    cost_price: float = Field(default=0, ge=0)
    sale_price: float = Field(default=0, ge=0)


class PartCreate(PartBase):
    pass


class PartUpdate(BaseModel):
    name: Optional[str] = None
    article: Optional[str] = None
    quantity: Optional[int] = None
    cost_price: Optional[float] = None
    sale_price: Optional[float] = None


class PartRead(PartBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PartMovement(BaseModel):
    """Движение запчасти: приход/расход/списание"""
    type: str = Field(..., description="Тип: income, expense, write_off")
    quantity: int = Field(..., gt=0)
    order_id: Optional[int] = None  # Для списания в заказ
    master_id: Optional[int] = None  # Мастер, с которого списывается запчасть


class WriteOffRead(BaseModel):
    """История списания запчасти"""
    id: int
    part_name: str
    article: str
    quantity: int
    price: float
    total: float
    order_id: int
    master_id: Optional[int]
    master_name: Optional[str]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
