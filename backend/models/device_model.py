"""
Модель справочника моделей устройств
Привязка моделей к брендам
"""

from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from backend.models.brand import Brand
    from backend.models.order import Order


class DeviceModelBase(SQLModel):
    """Базовая модель"""
    name: str = Field(..., description="Название модели", max_length=255)
    brand_id: Optional[int] = Field(None, foreign_key="brands.id", description="Бренд")
    is_active: bool = Field(default=True, description="Активна")
    category: Optional[str] = Field(None, description="Категория", max_length=100)


class DeviceModel(DeviceModelBase, table=True):
    """Модель устройства"""
    __tablename__ = "device_models"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Связи
    brand: Optional["Brand"] = Relationship(back_populates="models")
    orders: list["Order"] = Relationship(back_populates="model")


class DeviceModelCreate(DeviceModelBase):
    """Создание модели"""
    pass


class DeviceModelRead(DeviceModelBase):
    """Просмотр модели"""
    id: int
    brand_name: Optional[str] = None


class DeviceModelUpdate(SQLModel):
    """Обновление модели"""
    name: Optional[str] = Field(None, max_length=255)
    brand_id: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)
