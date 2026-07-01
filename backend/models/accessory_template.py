"""
Модель: Справочник комплектаций
"""
from typing import Optional
from sqlmodel import SQLModel, Field


class AccessoryTemplate(SQLModel, table=True):
    """Шаблон комплектации"""
    __tablename__ = "accessory_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=300, unique=True, index=True, description="Название комплектации")
    is_active: bool = Field(default=True, description="Активна")

    def __repr__(self):
        return f"<AccessoryTemplate {self.name}>"


class AccessoryTemplateCreate(SQLModel):
    """Создание комплектации"""
    name: str = Field(max_length=300)
    is_active: bool = Field(default=True)


class AccessoryTemplateRead(SQLModel):
    """Просмотр комплектации"""
    id: int
    name: str
    is_active: bool


class AccessoryTemplateUpdate(SQLModel):
    """Обновление комплектации"""
    name: Optional[str] = Field(None, max_length=300)
    is_active: Optional[bool] = None
