"""
Маршруты: Услуги
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.service import Service, ServiceStatus
from core.logging import logger

router = APIRouter(prefix="/api/services", tags=["Услуги"])


@router.get("/", summary="Список услуг")
def get_services(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Service)
    
    if status:
        query = query.where(Service.status == ServiceStatus(status))
    if search:
        query = query.where(Service.name.ilike(f"%{search}%"))
    
    query = query.offset(skip).limit(limit).order_by(Service.id.desc())
    services = session.exec(query).all()
    
    total = session.exec(select(Service)).all()
    
    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "price": s.price,
                "status": s.status.value,
                "duration_minutes": s.duration_minutes,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in services
        ],
        "total": len(total),
    }


@router.post("/", summary="Создать услугу")
def create_service(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = Service(
        name=data["name"],
        description=data.get("description", ""),
        price=data.get("price", 0),
        status=ServiceStatus(data.get("status", "active")),
        duration_minutes=data.get("duration_minutes"),
    )
    session.add(service)
    session.commit()
    session.refresh(service)
    logger.info(f"Услуга создана: {service.name}")
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "price": service.price,
        "status": service.status.value,
        "duration_minutes": service.duration_minutes,
    }


@router.patch("/{service_id}", summary="Обновить услугу")
def update_service(
    service_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = session.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    for key in ["name", "description", "price", "status", "duration_minutes"]:
        if key in data:
            setattr(service, key, data[key])
    
    session.add(service)
    session.commit()
    session.refresh(service)
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "price": service.price,
        "status": service.status.value,
        "duration_minutes": service.duration_minutes,
    }


@router.delete("/{service_id}", summary="Удалить услугу")
def delete_service(
    service_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    service = session.get(Service, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    session.delete(service)
    session.commit()
    return {"message": f"Услуга '{service.name}' удалена"}
