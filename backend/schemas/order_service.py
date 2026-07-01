"""
Схемы для OrderService
"""
from typing import Optional
from pydantic import BaseModel, Field


class OrderServiceCreate(BaseModel):
    service_id: Optional[int] = None
    service_name: str = Field(..., max_length=200)
    price: float = Field(default=0, ge=0)
    quantity: Optional[int] = Field(default=1, ge=1)
    comment: Optional[str] = Field(None, max_length=1000)


class OrderServiceRead(BaseModel):
    id: int
    order_id: int
    service_id: Optional[int] = None
    service_name: str
    price_at_order: float
    quantity: int
    comment: Optional[str] = None
    
    class Config:
        from_attributes = True
