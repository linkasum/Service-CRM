"""
Схемы для OrderPart
"""
from typing import Optional
from pydantic import BaseModel, Field


class OrderPartCreate(BaseModel):
    part_id: Optional[int] = None
    name: str = Field(..., max_length=200)
    cost_price: float = Field(default=0, ge=0)
    sale_price: float = Field(default=0, ge=0)
    quantity: int = Field(default=1, ge=1)


class OrderPartRead(BaseModel):
    id: int
    order_id: int
    part_id: int
    quantity: int
    price_at_order: float
    
    class Config:
        from_attributes = True
