"""
Маршруты для комментариев к заказам
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order_comment import OrderComment
from models.order import Order
from core.logging import logger

router = APIRouter(
    prefix="/api/orders/{order_id}/comments", tags=["Комментарии заказов"]
)


@router.get("/", summary="Список комментариев заказа")
def get_order_comments(
    order_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    comments = session.exec(
        select(OrderComment)
        .where(OrderComment.order_id == order_id)
        .order_by(OrderComment.created_at.desc())
        .offset(skip)
        .limit(limit)
    ).all()

    return [
        {
            "id": c.id,
            "order_id": c.order_id,
            "user_id": c.user_id,
            "username": c.username,
            "role_name": c.role_name,
            "text": c.text,
            "photo_file_id": c.photo_file_id,
            "is_system": c.is_system,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in comments
    ]


@router.post("/", summary="Добавить комментарий")
def add_comment(
    order_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        username=current_user.username,
        role_name=current_user.role.name if current_user.role else "",
        text=data.get("text", ""),
        photo_file_id=data.get("photo_file_id"),
        is_system=data.get("is_system", False),
    )

    session.add(comment)
    session.commit()
    session.refresh(comment)

    logger.info(f"Комментарий к заказу #{order_id} от {current_user.username}")
    return comment


@router.delete("/{comment_id}", summary="Удалить комментарий")
def delete_comment(
    order_id: int,
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    comment = session.get(OrderComment, comment_id)
    if not comment or comment.order_id != order_id:
        raise HTTPException(status_code=404, detail="Комментарий не найден")

    # Удалять можно только свои или админ
    if comment.user_id != current_user.id and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    session.delete(comment)
    session.commit()
    return {"message": "Комментарий удалён"}


@router.post("/system", summary="Системный комментарий (смена статуса)")
def add_system_comment(
    order_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Системное сообщение о смене статуса, выдаче, начислении ЗП"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        username=current_user.username,
        role_name=current_user.role.name if current_user.role else "",
        text=data.get("text", ""),
        is_system=True,
    )

    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment
