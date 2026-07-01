from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.order_part import OrderPart
from models.part import Part
from core.logging import logger

router = APIRouter(prefix='/api/order-parts', tags=['Запчасти в заказе'])

@router.delete('/{op_id}', summary='Удалить запчасть из заказа')
def delete_order_part(op_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    op = session.get(OrderPart, op_id)
    if not op:
        raise HTTPException(status_code=404, detail='Не найдено')
    order = session.get(Order, op.order_id)
    part = session.get(Part, op.part_id)
    if part:
        part.quantity += op.quantity
        session.add(part)
    if order:
        cost = op.price_at_order * op.quantity
        order.parts_cost = max((order.parts_cost or 0) - cost, 0)
        order.total_cost = max((order.total_cost or 0) - cost, 0)
        session.add(order)
    session.delete(op)
    session.commit()
    return {'message': 'Удалено'}
