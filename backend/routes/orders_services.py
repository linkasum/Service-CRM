"""
API для услуг в заказе
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.order_service import OrderService
from models.service import Service
from schemas.order_service import OrderServiceCreate, OrderServiceRead

router = APIRouter(prefix="/api/orders/{order_id}/services", tags=["Услуги в заказе"])


@router.post("/", summary="Добавить услугу в заказ")
def add_service_to_order(
    order_id: int,
    service_data: OrderServiceCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Добавить услугу к заказу"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Если указан service_id - берём из справочника
    if service_data.service_id:
        service = session.get(Service, service_data.service_id)
        if not service:
            raise HTTPException(status_code=404, detail="Услуга не найдена")
        service_name = service.name
        price = service.price
    else:
        service_name = service_data.service_name
        price = service_data.price
    
    # Создаём запись
    order_service = OrderService(
        order_id=order_id,
        service_id=service_data.service_id,
        service_name=service_name,
        price_at_order=price,
        quantity=service_data.quantity or 1,
        comment=service_data.comment,
    )
    session.add(order_service)
    
    # Обновляем work_cost в заказе
    order.work_cost = (order.work_cost or 0) + (price * (service_data.quantity or 1))
    order.total_cost = (order.total_cost or 0) + (price * (service_data.quantity or 1))
    
    session.commit()
    session.refresh(order_service)
    
    return order_service


@router.get("/", summary="Список услуг заказа")
def get_order_services(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить все услуги заказа"""
    services = session.exec(
        select(OrderService).where(OrderService.order_id == order_id)
    ).all()
    return services


@router.delete("/{service_id}", summary="Удалить услугу из заказа")
def remove_service_from_order(
    order_id: int,
    service_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить услугу из заказа"""
    order_service = session.get(OrderService, service_id)
    if not order_service:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    
    # Обновляем work_cost в заказе
    order = session.get(Order, order_id)
    if order:
        order.work_cost = (order.work_cost or 0) - (order_service.price_at_order * order_service.quantity)
        order.total_cost = (order.total_cost or 0) - (order_service.price_at_order * order_service.quantity)
    
    session.delete(order_service)
    session.commit()
    
    return {"message": "Услуга удалена"}
