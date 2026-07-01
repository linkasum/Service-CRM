"""
Маршруты: Платежи по заказам
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.order_payment import OrderPayment, PaymentType, PaymentStatus, PaymentMethod
from core.logging import logger

router = APIRouter(prefix="/api/payments", tags=["Платежи"])


@router.get("/", summary="Список платежей")
def get_payments(
    order_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    payment_type: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(OrderPayment)
    
    if order_id is not None:
        query = query.where(OrderPayment.order_id == order_id)
    if user_id is not None:
        query = query.where(OrderPayment.created_by_id == user_id)
    if payment_type:
        query = query.where(OrderPayment.payment_type == PaymentType(payment_type))
    
    query = query.offset(skip).limit(limit).order_by(OrderPayment.created_at.desc())
    payments = session.exec(query).all()
    
    result = []
    for p in payments:
        result.append({
            "id": p.id,
            "order_id": p.order_id,
            "payment_type": p.payment_type.value,
            "amount": p.amount,
            "method": p.method.value if p.method else None,
            "status": p.status.value,
            "comment": p.comment,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "created_by_id": p.created_by_id,
            "created_by_username": p.order.acceptor.username if p.order and p.order.acceptor else None,
        })
    
    return result


@router.get("/{payment_id}", summary="Платёж по ID")
def get_payment(
    payment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    payment = session.get(OrderPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "payment_type": payment.payment_type.value,
        "amount": payment.amount,
        "method": payment.method.value,
        "status": payment.status.value,
        "comment": payment.comment,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
        "created_by_id": payment.created_by_id,
    }


@router.post("/", summary="Создать платёж")
def create_payment(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order_id = data.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="order_id обязателен")
    
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    payment_type = PaymentType(data.get("payment_type", "prepayment"))
    if payment_type == PaymentType.final and order.status in ("issued", "issued_br"):
        raise HTTPException(status_code=400, detail="Заказ уже выдан, оплата невозможна")
    
    amount = data.get("amount", 0)
    
    # Конвертируем в число (может прийти как строка из frontend)
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Неверный формат суммы")
    
    # Проверяем что сумма положительная
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Сумма должна быть > 0")

    method = PaymentMethod(data.get("method", "cash"))
    comment = data.get("comment", "")

    # Для возврата — сумма отрицательная
    if payment_type == PaymentType.refund:
        amount = -abs(amount)
    
    payment = OrderPayment(
        order_id=order_id,
        payment_type=payment_type,
        amount=amount,
        method=method,
        status=PaymentStatus.completed,
        comment=comment,
        created_by_id=current_user.id,
    )
    
    session.add(payment)

    # Создаём транзакцию в кассе (для всех платежей)
    from models.cash_shift import CashShift
    from models.cash_transaction import CashTransaction, TransactionType
    
    # Берём активную смену
    active_shift = session.exec(
        select(CashShift).where(CashShift.is_open == True).order_by(CashShift.opened_at.desc())
    ).first()
    
    if not active_shift:
        raise HTTPException(
            status_code=400,
            detail="Нет активной кассовой смены. Откройте смену перед оплатой."
        )
    
    # Определяем тип транзакции
    if payment_type in [PaymentType.prepayment, PaymentType.final]:
        transaction_type = TransactionType.income
        cash_amount = amount  # Положительная
        description = f"Оплата по заказу #{order_id}"
    elif payment_type == PaymentType.refund:
        transaction_type = TransactionType.expense
        cash_amount = -abs(amount)  # Отрицательная
        description = f"Возврат по заказу #{order_id}"
    else:
        # Для expense и других
        transaction_type = TransactionType.expense
        cash_amount = -abs(amount)
        description = f"Платёж по заказу #{order_id}"

    # Определяем метод оплаты (cash/card)
    payment_method_enum = None
    if method:
        from models.cash_transaction import PaymentMethod as CashPaymentMethod
        payment_method_enum = CashPaymentMethod(method) if method in ['cash', 'card'] else CashPaymentMethod.cash

    cash_transaction = CashTransaction(
        shift_id=active_shift.id,
        order_id=order_id,
        transaction_type=transaction_type,
        amount=cash_amount,
        payment_method=payment_method_enum or CashPaymentMethod.cash,
        comment=comment or description,
        created_by=current_user.id,
    )
    session.add(cash_transaction)
    
    # Пересчёт оплаченной суммы заказа
    _recalculate_paid(session, order_id)

    # Для возврата — пересчитываем зарплату мастера
    if payment_type == PaymentType.refund:
        from models.salary_record import SalaryRecord
        
        # Пересчёт зарплаты мастера (пропорционально возврату)
        # Находим начисленную зарплату для этого заказа
        existing_salary = session.exec(
            select(SalaryRecord).where(
                SalaryRecord.order_id == order_id,
                SalaryRecord.status == "accrued"
            )
        ).first()
        
        if existing_salary and order.total_cost and order.total_cost > 0:
            # Пропорциональный пересчёт
            refund_ratio = abs(amount) / order.total_cost
            salary_deduction = existing_salary.calculated_amount * refund_ratio
            
            # Создаём запись с отрицательной суммой (вычет)
            salary_refund = SalaryRecord(
                user_id=existing_salary.user_id,
                order_id=order_id,
                calculated_amount=-salary_deduction,
                status="accrued",
                period_start=existing_salary.period_start,
                period_end=existing_salary.period_end,
                comment=f"Возврат по заказу #{order_id} (-{salary_deduction:.2f}₽)",
            )
            session.add(salary_refund)
            logger.info(f"Пересчёт зарплаты мастеру: вычет {salary_deduction:.2f}₽ за возврат по заказу #{order_id}")
    
    # Системный комментарий
    type_labels = {
        PaymentType.prepayment: "Предоплата",
        PaymentType.final: "Оплата",
        PaymentType.refund: "Возврат",
        PaymentType.expense: "Расход",
    }
    system_comment = f"{type_labels[payment_type]}: {abs(amount):.2f}₽ ({method.value})"
    if comment:
        system_comment += f" — {comment}"
    
    from models.order_comment import OrderComment
    system_cmt = OrderComment(
        order_id=order_id,
        text=system_comment,
        is_system=True,
        user_id=current_user.id,
        username=current_user.username,
    )
    session.add(system_cmt)
    
    session.commit()
    session.refresh(payment)
    
    logger.info(f"Платёж создан: {payment_type.value} {amount}₽ для заказа #{order_id}")
    
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "payment_type": payment.payment_type.value,
        "amount": payment.amount,
        "method": payment.method.value,
        "status": payment.status.value,
        "comment": payment.comment,
        "created_at": payment.created_at.isoformat(),
        "created_by_id": payment.created_by_id,
    }


@router.patch("/{payment_id}", summary="Обновить платёж")
def update_payment(
    payment_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    payment = session.get(OrderPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    
    if "status" in data:
        payment.status = PaymentStatus(data["status"])
    if "comment" in data:
        payment.comment = data["comment"]
    
    session.add(payment)
    session.commit()
    session.refresh(payment)
    
    return {
        "id": payment.id,
        "status": payment.status.value,
        "comment": payment.comment,
    }


@router.delete("/{payment_id}", summary="Удалить платёж")
def delete_payment(
    payment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    payment = session.get(OrderPayment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")
    
    order_id = payment.order_id
    session.delete(payment)
    
    # Пересчёт
    _recalculate_paid(session, order_id)
    
    session.commit()
    return {"message": f"Платёж #{payment_id} удалён"}


@router.get("/order/{order_id}/summary", summary="Сводка платежей по заказу")
def payment_summary(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    payments = session.exec(
        select(OrderPayment).where(
            OrderPayment.order_id == order_id,
            OrderPayment.status == PaymentStatus.completed,
        )
    ).all()

    # Считаем все платежи: refund и expense вычитаются (у них отрицательная сумма)
    total_paid = sum(p.amount for p in payments if p.payment_type not in (PaymentType.expense, PaymentType.refund))
    total_expenses = sum(abs(p.amount) for p in payments if p.payment_type == PaymentType.expense)
    total_refunds = sum(abs(p.amount) for p in payments if p.payment_type == PaymentType.refund)
    
    # Итоговая оплаченная сумма = платежи - расходы - возвраты
    net_paid = total_paid - total_expenses - total_refunds
    
    remaining = (order.total_cost or 0) - net_paid
    total_cost_for_percent = order.total_cost if order.total_cost and order.total_cost > 0 else net_paid if net_paid > 0 else 1

    return {
        "order_id": order_id,
        "total_cost": order.total_cost or 0,
        "total_paid": net_paid,  # Теперь показываем чистую сумму
        "total_expenses": total_expenses,
        "total_refunds": total_refunds,
        "remaining": remaining,
        "paid_percent": round(net_paid / total_cost_for_percent * 100, 1),
        "is_fully_paid": remaining <= 0,
        "payments_count": len(payments),
    }


def _recalculate_paid(session: Session, order_id: int):
    """Пересчитать оплаченную сумму заказа"""
    payments = session.exec(
        select(OrderPayment).where(
            OrderPayment.order_id == order_id,
            OrderPayment.status == PaymentStatus.completed,
            OrderPayment.payment_type != PaymentType.expense,
        )
    ).all()
    
    total_paid = sum(p.amount for p in payments)
    order = session.get(Order, order_id)
    if order:
        order.paid_amount = total_paid  # type: ignore
        session.add(order)
