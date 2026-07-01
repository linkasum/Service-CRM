"""
API: Справочник моделей устройств
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.device_model import DeviceModel, DeviceModelCreate, DeviceModelRead, DeviceModelUpdate
from models.brand import Brand

router = APIRouter(prefix="/api/models", tags=["Модели устройств"])


@router.get("/", response_model=List[DeviceModelRead])
def get_models(
    brand_id: Optional[int] = Query(None, description="Фильтр по бренду"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список моделей"""
    query = select(DeviceModel).where(DeviceModel.is_active == True)
    
    if brand_id:
        query = query.where(DeviceModel.brand_id == brand_id)
    
    if search:
        query = query.where(DeviceModel.name.ilike(f"%{search}%"))
    
    query = query.order_by(DeviceModel.name)
    results = session.exec(query)
    
    models = []
    for m in results:
        brand_name = None
        if m.brand:
            brand_name = m.brand.name
        
        models.append(DeviceModelRead(
            id=m.id,
            name=m.name,
            brand_id=m.brand_id,
            brand_name=brand_name,
            is_active=m.is_active,
            category=m.category,
        ))
    
    return models


@router.post("/", response_model=DeviceModelRead)
def create_model(
    model_data: DeviceModelCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать модель"""
    # Проверяем бренд если указан
    if model_data.brand_id:
        brand = session.get(Brand, model_data.brand_id)
        if not brand:
            raise HTTPException(status_code=404, detail="Бренд не найден")
    
    model = DeviceModel.model_validate(model_data)
    session.add(model)
    session.commit()
    session.refresh(model)
    
    brand_name = None
    if model.brand:
        brand_name = model.brand.name
    
    return DeviceModelRead(
        id=model.id,
        name=model.name,
        brand_id=model.brand_id,
        brand_name=brand_name,
        is_active=model.is_active,
        category=model.category,
    )


@router.get("/{model_id}", response_model=DeviceModelRead)
def get_model(
    model_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить модель по ID"""
    model = session.get(DeviceModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    brand_name = None
    if model.brand:
        brand_name = model.brand.name
    
    return DeviceModelRead(
        id=model.id,
        name=model.name,
        brand_id=model.brand_id,
        brand_name=brand_name,
        is_active=model.is_active,
        category=model.category,
    )


@router.patch("/{model_id}", response_model=DeviceModelRead)
def update_model(
    model_id: int,
    model_data: DeviceModelUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить модель"""
    model = session.get(DeviceModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    update_data = model_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(model, key, value)
    
    session.add(model)
    session.commit()
    session.refresh(model)
    
    brand_name = None
    if model.brand:
        brand_name = model.brand.name
    
    return DeviceModelRead(
        id=model.id,
        name=model.name,
        brand_id=model.brand_id,
        brand_name=brand_name,
        is_active=model.is_active,
        category=model.category,
    )


@router.delete("/{model_id}")
def delete_model(
    model_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить модель"""
    model = session.get(DeviceModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    session.delete(model)
    session.commit()
    
    return {"ok": True}
