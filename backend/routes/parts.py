"""
Parts маршруты: управление складом запчастей
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.part import Part
from models.order_part import OrderPart
from models.order import Order
from models.order_comment import OrderComment
from models.order_payment import OrderPayment
from models.user import User
from schemas.part import PartCreate, PartUpdate, PartRead, PartMovement, WriteOffRead
from core.logging import logger

router = APIRouter(prefix="/api/parts", tags=["Склад запчастей"])


@router.get("/", response_model=List[PartRead], summary="Список запчастей")
def get_parts(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список запчастей с поиском"""
    query = select(Part)
    
    if search:
        query = query.where(
            (Part.name.ilike(f"%{search}%")) |
            (Part.article.ilike(f"%{search}%"))
        )
    
    query = query.offset(skip).limit(limit)
    return session.exec(query).all()


@router.get("/write-offs", response_model=List[WriteOffRead], summary="История списаний")
def get_write_offs(
    part_id: Optional[int] = Query(None, description="Фильтр по запчасти"),
    limit: int = Query(50, ge=1, le=500),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить историю списаний запчастей (OrderPart записи)"""
    query = select(OrderPart, Part, User).join(Part, OrderPart.part_id == Part.id).outerjoin(User, OrderPart.master_id == User.id)

    if part_id is not None:
        query = query.where(OrderPart.part_id == part_id)

    query = query.order_by(OrderPart.created_at.desc()).limit(limit)

    rows = session.exec(query).all()

    result = []
    for order_part, part, master in rows:
        result.append(WriteOffRead(
            id=order_part.id,
            part_name=part.name,
            article=part.article,
            quantity=order_part.quantity,
            price=order_part.price_at_order,
            total=order_part.price_at_order * order_part.quantity,
            order_id=order_part.order_id,
            master_id=order_part.master_id,
            master_name=master.username if master else None,
            created_at=order_part.created_at,
        ))

    return result


@router.get("/{part_id}", response_model=PartRead, summary="Детали запчасти")
def get_part(
    part_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить детали конкретной запчасти"""
    part = session.get(Part, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    return part


@router.post("/", response_model=PartRead, summary="Добавить запчасть")
def create_part(
    part_data: PartCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Добавить новую запчасть на склад"""
    # Проверка уникальности артикула
    existing = session.exec(select(Part).where(Part.article == part_data.article)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Запчасть с таким артикулом уже существует")
    
    part = Part.model_validate(part_data)
    session.add(part)
    session.commit()
    session.refresh(part)
    
    logger.info(f"Добавлена запчасть: {part.name} ({part.article}), кол-во: {part.quantity}")
    return part


@router.patch("/{part_id}", response_model=PartRead, summary="Обновить запчасть")
def update_part(
    part_id: int,
    part_data: PartUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить данные запчасти"""
    part = session.get(Part, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    
    update_data = part_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(part, key, value)
    
    part.updated_at = datetime.utcnow()
    
    session.add(part)
    session.commit()
    session.refresh(part)
    
    return part


@router.post("/{part_id}/movement", response_model=PartRead, summary="Движение запчасти")
def part_movement(
    part_id: int,
    movement: PartMovement,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Движение запчасти: приход (income), расход (expense), списание (write_off).
    
    При списании в заказ — создаётся запись OrderPart.
    """
    part = session.get(Part, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    
    if movement.type == "income":
        part.quantity += movement.quantity
        
    elif movement.type == "expense":
        if part.quantity < movement.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно на складе. Доступно: {part.quantity}"
            )
        part.quantity -= movement.quantity
        
    elif movement.type == "write_off":
        if not movement.order_id:
            raise HTTPException(status_code=400, detail="Для списания необходим order_id")
        
        order = session.get(Order, movement.order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        
        if part.quantity < movement.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно на складе. Доступно: {part.quantity}"
            )
        
        part.quantity -= movement.quantity
        
        # Определить имя мастера
        master_name = None
        if movement.master_id:
            master = session.get(User, movement.master_id)
            master_name = master.username if master else None

        # Создать запись OrderPart
        order_part = OrderPart(
            order_id=movement.order_id,
            part_id=part_id,
            quantity=movement.quantity,
            price_at_order=part.sale_price,
            master_id=movement.master_id,
        )
        session.add(order_part)
        
        # Обновить стоимость запчастей и общую сумму в заказе
        added_cost = part.sale_price * movement.quantity
        order.parts_cost = (order.parts_cost or 0) + added_cost
        order.total_cost = (order.total_cost or 0) + added_cost
        session.add(order)

        # Вычитаем стоимость запчасти из баланса мастера (40% от цены запчасти)
        if movement.master_id:
            from models.salary_record import SalaryRecord
            master_deduction = SalaryRecord(
                user_id=movement.master_id,
                order_id=movement.order_id,
                calculated_amount=-(added_cost * 0.4),
                status="deducted",
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
                comment=f"Списание запчасти: {part.name} x{movement.quantity} = {added_cost}руб",
            )
            session.add(master_deduction)

        # Системный комментарий
        comment_text = f"📦 Списана запчасть: {part.name} × {movement.quantity} = {added_cost}₽"
        if master_name:
            comment_text += f" (мастер: {master_name})"
        part_comment = OrderComment(
            order_id=movement.order_id,
            user_id=current_user.id,
            username=current_user.username,
            role_name=current_user.role.name if current_user.role else "",
            text=comment_text,
            is_system=True,
        )
        session.add(part_comment)
        
    else:
        raise HTTPException(status_code=400, detail="Недопустимый тип движения")
    
    part.updated_at = datetime.utcnow()
    session.add(part)
    session.commit()
    session.refresh(part)
    
    logger.info(
        f"Движение запчасти {part.name} ({part.article}): "
        f"{movement.type}, кол-во: {movement.quantity}"
    )
    
    return part


@router.delete("/{part_id}", summary="Удалить запчасть")
def delete_part(
    part_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить запчасть со склада"""
    part = session.get(Part, part_id)
    if not part:
        raise HTTPException(status_code=404, detail="Запчасть не найдена")
    
    session.delete(part)
    session.commit()
    
    logger.info(f"Удалена запчасть: {part.name} ({part.article})")
    return {"message": f"Запчасть '{part.name}' удалена"}
