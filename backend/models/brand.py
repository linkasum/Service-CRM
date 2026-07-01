"""
Модель: Бренд устройства
"""
from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from backend.models.device_model import DeviceModel


class Brand(SQLModel, table=True):
    __tablename__ = "brands"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    is_active: bool = Field(default=True)

    # Связи
    models: list["DeviceModel"] = Relationship(back_populates="brand")

    def __repr__(self):
        return f"<Brand {self.name}>"
