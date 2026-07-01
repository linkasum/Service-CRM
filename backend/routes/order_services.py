"""
Маршруты: Услуги в заказе
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order_service import OrderService
from models.order import Order
from models.order_comment import OrderComment
from core.logging import logger

router = APIRouter(prefix="/api/order-services", tags=["Услуги в заказе"])


@router.post("/", summary="Добавить услугу в заказ")
def add_service_to_order(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order_id = data.get("order_id")
    service_id = data.get("service_id")

    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    os_item = OrderService(
        order_id=order_id,
        service_id=service_id,
        service_name=data.get("service_name", ""),
        price_at_order=data.get("price_at_order", 0),
        quantity=data.get("quantity", 1),
        comment=data.get("comment", ""),
    )
    session.add(os_item)

    # Обновляем work_cost и total_cost заказа
    price = float(data.get("price_at_order", 0))
    qty = int(data.get("quantity", 1))
    order.work_cost = (order.work_cost or 0) + price * qty
    order.total_cost = (order.total_cost or 0) + price * qty
    session.add(order)

    # Системный комментарий
    svc_comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        username=current_user.username,
        role_name=current_user.role.name if current_user.role else "",
        text=f"🔧 Добавлена услуга: {os_item.service_name} × {os_item.quantity} = {os_item.price_at_order * os_item.quantity}₽",
        is_system=True,
    )
    session.add(svc_comment)

    session.commit()
    session.refresh(os_item)

    logger.info(f"Услуга добавлена в заказ #{order_id}: {os_item.service_name}")

    return {
        "id": os_item.id,
        "order_id": os_item.order_id,
        "service_name": os_item.service_name,
        "price_at_order": os_item.price_at_order,
        "quantity": os_item.quantity,
        "comment": os_item.comment,
    }


@router.delete("/{os_id}", summary="Удалить услугу из заказа")
def remove_service_from_order(
    os_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    os_item = session.get(OrderService, os_id)
    if not os_item:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    order = session.get(Order, os_item.order_id)
    if order:
        order.work_cost = max(0, (order.work_cost or 0) - os_item.price_at_order * os_item.quantity)
        order.total_cost = max(0, (order.total_cost or 0) - os_item.price_at_order * os_item.quantity)
        session.add(order)

    # Системный комментарий
    if order:
        svc_comment = OrderComment(
            order_id=os_item.order_id,
            user_id=current_user.id,
            username=current_user.username,
            role_name=current_user.role.name if current_user.role else "",
            text=f"❌ Удалена услуга: {os_item.service_name} × {os_item.quantity}",
            is_system=True,
        )
        session.add(svc_comment)

    session.delete(os_item)
    session.commit()

    return {"message": "Услуга удалена из заказа"}
