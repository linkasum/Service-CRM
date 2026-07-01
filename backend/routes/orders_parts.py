"""
API для запчастей в заказе
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.order_part import OrderPart
from models.part import Part
from schemas.order_part import OrderPartCreate, OrderPartRead

router = APIRouter(prefix="/api/orders/{order_id}/parts", tags=["Запчасти в заказе"])


@router.post("/", summary="Добавить запчасть в заказ")
def add_part_to_order(
    order_id: int,
    part_data: OrderPartCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Добавить запчасть к заказу"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    # Если указан part_id - берём из справочника
    if part_data.part_id:
        part = session.get(Part, part_data.part_id)
        if not part:
            raise HTTPException(status_code=404, detail="Запчасть не найдена")
        part_name = part.name
        cost_price = part.cost_price
        sale_price = part.sale_price
        # Уменьшаем количество на складе
        if part.quantity < part_data.quantity:
            raise HTTPException(status_code=400, detail=f"Недостаточно запчастей на складе. Доступно: {part.quantity}")
        part.quantity -= part_data.quantity
    else:
        part_name = part_data.name
        cost_price = part_data.cost_price
        sale_price = part_data.sale_price
    
    # Создаём запись
    order_part = OrderPart(
        order_id=order_id,
        part_id=part_data.part_id,
        quantity=part_data.quantity,
        price_at_order=cost_price,
    )
    session.add(order_part)
    
    # Обновляем parts_cost в заказе
    order.parts_cost = (order.parts_cost or 0) + (cost_price * part_data.quantity)
    order.total_cost = (order.total_cost or 0) + (cost_price * part_data.quantity)
    
    session.commit()
    session.refresh(order_part)
    
    return order_part


@router.get("/", summary="Список запчастей заказа")
def get_order_parts(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить все запчасти заказа"""
    parts = session.exec(
        select(OrderPart).where(OrderPart.order_id == order_id)
    ).all()
    return parts


@router.delete("/{part_id}", summary="Удалить запчасть из заказа")
def remove_part_from_order(
    order_id: int,
    part_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить запчасть из заказа"""
    order_part = session.get(OrderPart, part_id)
    if not order_part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    
    # Обновляем parts_cost в заказе
    order = session.get(Order, order_id)
    if order:
        order.parts_cost = (order.parts_cost or 0) - order_part.price_at_order
        order.total_cost = (order.total_cost or 0) - order_part.price_at_order
    
    session.delete(order_part)
    session.commit()
    
    return {"message": "Запчасть удалена"}
