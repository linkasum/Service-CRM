"""
Модель: Запчасть (склад)
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class Part(SQLModel, table=True):
    __tablename__ = "parts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=300, index=True)
    article: str = Field(max_length=100, unique=True, index=True)
    quantity: int = Field(default=0, ge=0)
    cost_price: float = Field(default=0, ge=0)
    sale_price: float = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    order_parts: List["OrderPart"] = Relationship(back_populates="part")

    def __repr__(self):
        return f"<Part {self.name} ({self.article})>"
