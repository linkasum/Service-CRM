"""
Маршруты: Касса — смены, приход, расход, корректировки
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, or_
from datetime import datetime, date, time, timedelta

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.cash_shift import CashShift
from models.cash_transaction import CashTransaction, TransactionType, PaymentMethod
from models.order import Order
from models.work_schedule import WorkSchedule
from models.salary_record import SalaryRecord
from models.salary_config import SalaryConfig, SalaryType, SalaryPeriod
from core.logging import logger

router = APIRouter(prefix="/api/cash", tags=["Касса"])


def calculate_shift_balance(session: Session, shift: CashShift) -> dict:
    transactions = session.exec(
        select(CashTransaction).where(CashTransaction.shift_id == shift.id)
    ).all()
    # Все транзакции
    income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income)
    expense = sum(abs(t.amount) for t in transactions if t.transaction_type in (TransactionType.expense, TransactionType.cashout))
    adjustments = sum(t.amount for t in transactions if t.transaction_type == TransactionType.adjustment)
    # Только наличные
    cash_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income and t.payment_method == PaymentMethod.cash)
    cash_expense = sum(abs(t.amount) for t in transactions if t.transaction_type in (TransactionType.expense, TransactionType.cashout) and t.payment_method == PaymentMethod.cash)
    # Только безнал
    card_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income and t.payment_method == PaymentMethod.card)

    current_balance = shift.initial_amount + income - expense + adjustments
    cash_balance = shift.initial_amount + cash_income - cash_expense
    return {
        "income": income,
        "expense": expense,
        "adjustments": adjustments,
        "current_balance": current_balance,
        "cash_income": cash_income,
        "cash_expense": cash_expense,
        "card_income": card_income,
        "cash_balance": cash_balance,
        "transactions_count": len(transactions),
    }


def get_last_closed_shift(session: Session) -> Optional[CashShift]:
    shift = session.exec(
        select(CashShift)
        .where(CashShift.is_open == False, CashShift.closed_at.isnot(None))
        .order_by(CashShift.closed_at.desc(), CashShift.id.desc())
        .limit(1)
    ).first()
    if shift:
        return shift
    return session.exec(
        select(CashShift)
        .where(CashShift.is_open == False)
        .order_by(CashShift.opened_at.desc(), CashShift.id.desc())
        .limit(1)
    ).first()


@router.get("/shift/current", summary="Текущая открытая смена")
def get_current_shift(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить текущую открытую смену или None"""
    shift = session.exec(
        select(CashShift).where(CashShift.is_open == True).order_by(CashShift.opened_at.desc(), CashShift.id.desc()).limit(1)
    ).first()
    
    if not shift:
        return None
    
    balance = calculate_shift_balance(session, shift)
    
    return {
        "id": shift.id,
        "opened_at": shift.opened_at.isoformat(),
        "opened_by": shift.opened_by,
        "initial_amount": shift.initial_amount,
        "income": balance["income"],
        "expense": balance["expense"],
        "adjustments": balance["adjustments"],
        "current_balance": balance["current_balance"],
        "cash_income": balance["cash_income"],
        "card_income": balance["card_income"],
        "cash_balance": balance["cash_balance"],
        "transactions_count": balance["transactions_count"],
    }


@router.post("/shift/open", summary="Открыть смену")
def open_shift(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Открыть новую кассовую смену.
    initial_amount: начальный баланс (по умолчанию — остаток предыдущей закрытой смены)
    """
    # Проверяем что нет открытой смены
    existing = session.exec(
        select(CashShift).where(CashShift.is_open == True)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Уже есть открытая смена")
    
    # Всегда берём остаток предыдущей закрытой смены, игнорируем initial_amount из запроса
    prev_shift = get_last_closed_shift(session)
    initial_amount = prev_shift.final_amount if prev_shift else 0
    
    shift = CashShift(
        opened_by=current_user.id,
        initial_amount=initial_amount,
        is_open=True,
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    
    logger.info(f"Кассовая смена #{shift.id} открыта, начальный баланс: {initial_amount}₽")
    
    return {
        "id": shift.id,
        "opened_at": shift.opened_at.isoformat(),
        "initial_amount": shift.initial_amount,
    }


@router.post("/shift/close", summary="Закрыть смену")
def close_shift(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Закрыть текущую открытую смену.
    final_amount: фактический остаток в кассе (для сверки)
    """
    shift = session.exec(
        select(CashShift).where(CashShift.is_open == True)
    ).first()
    if not shift:
        raise HTTPException(status_code=400, detail="Нет открытой смены")
    
    transactions = session.exec(
        select(CashTransaction).where(CashTransaction.shift_id == shift.id)
    ).all()
    
    income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income)
    expense = sum(abs(t.amount) for t in transactions if t.transaction_type in (TransactionType.expense, TransactionType.cashout))
    adjustments = sum(t.amount for t in transactions if t.transaction_type == TransactionType.adjustment)
    cash_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income and t.payment_method == PaymentMethod.cash)
    card_income = sum(t.amount for t in transactions if t.transaction_type == TransactionType.income and t.payment_method == PaymentMethod.card)

    # Общий баланс (для статистики) и наличный баланс (для закрытия смены)
    total_balance = shift.initial_amount + income - expense + adjustments
    cash_balance = shift.initial_amount + cash_income - expense + adjustments

    if cash_balance < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Невозможно закрыть смену: наличный баланс отрицательный ({cash_balance:.2f}₽). Проверьте транзакции."
        )

    # При закрытии учитываем только наличные
    final_amount = data.get("final_amount", cash_balance)
    diff = final_amount - cash_balance
    
    shift.is_open = False
    shift.closed_at = datetime.utcnow()
    shift.closed_by = current_user.id
    shift.final_amount = final_amount
    
    session.add(shift)
    session.commit()
    
    logger.info(f"Кассовая смена #{shift.id} закрыта, итог: {final_amount}₽")

    # Начисление зарплаты по графику работы.
    # Рабочий день сервиса: 10:00-20:00. Берём дату открытия смены, а не
    # системную дату закрытия, чтобы позднее закрытие или тестовые смены не
    # начисляли зарплату за неправильный день.
    work_date = shift.opened_at.date() if shift.opened_at else date.today()
    scheduled = session.exec(
        select(WorkSchedule).where(WorkSchedule.date == work_date)
    ).all()

    accrued_salaries = []
    for ws in scheduled:
        user = session.get(User, ws.user_id)
        if not user or not user.salary_config_id:
            continue
        config = session.get(SalaryConfig, user.salary_config_id)
        if not config or not config.is_active:
            continue
        # Только per_shift + fixed
        if config.period != SalaryPeriod.per_shift or config.config_type != SalaryType.fixed:
            continue
        # Проверка дубля — ищем запись за рабочий день смены с меткой 'shift_auto'
        day_start = datetime.combine(work_date, time(hour=10))
        day_end = datetime.combine(work_date, time(hour=20))
        existing = session.exec(
            select(SalaryRecord).where(
                SalaryRecord.user_id == ws.user_id,
                SalaryRecord.period_start >= day_start,
                SalaryRecord.period_start <= day_end,
                SalaryRecord.comment.contains('shift_auto'),
            )
        ).first()
        if existing:
            continue
        record = SalaryRecord(
            user_id=ws.user_id,
            calculated_amount=config.fixed_amount,
            status='accrued',
            period_start=day_start,
            period_end=day_end,
            comment=f'shift_auto | Авто-начисление за смену #{shift.id} ({work_date})',
        )
        session.add(record)
        accrued_salaries.append({
            'user_id': ws.user_id,
            'user_name': user.full_name or user.username,
            'amount': config.fixed_amount,
        })

    if accrued_salaries:
        session.commit()
        logger.info(f'Начислена зарплата за смену #{shift.id}: {len(accrued_salaries)} сотрудникам')

    return {
        "id": shift.id,
        "initial_amount": shift.initial_amount,
        "income": income,
        "expense": expense,
        "cash_income": cash_income,
        "card_income": card_income,
        "total_balance": total_balance,
        "cash_balance": cash_balance,
        "final_amount": final_amount,
        "difference": diff,
        "transactions_count": len(transactions),
        "accrued_salaries": accrued_salaries,
    }


@router.get("/transactions", summary="Список транзакций")
def get_transactions(
    shift_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Список транзакций кассы"""
    query = select(CashTransaction)
    
    if shift_id:
        query = query.where(CashTransaction.shift_id == shift_id)
    else:
        # Если смена не указана — берём текущую открытую
        current_shift = session.exec(
            select(CashShift).where(CashShift.is_open == True).order_by(CashShift.opened_at.desc()).limit(1)
        ).first()
        if current_shift:
            query = query.where(CashTransaction.shift_id == current_shift.id)
    
    if transaction_type:
        query = query.where(CashTransaction.transaction_type == TransactionType(transaction_type))
    
    query = query.offset(skip).limit(limit).order_by(CashTransaction.created_at.desc())
    transactions = session.exec(query).all()
    
    result = []
    for t in transactions:
        result.append({
            "id": t.id,
            "shift_id": t.shift_id,
            "order_id": t.order_id,
            "transaction_type": t.transaction_type.value,
            "payment_method": t.payment_method.value if t.payment_method else "cash",
            "amount": t.amount,
            "comment": t.comment,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "created_by": t.created_by,
        })
    
    return result


@router.post("/transaction", summary="Провести транзакцию")
def create_transaction(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Провести транзакцию (приход, расход, корректировка, инкассация).
    amount: для расхода и инкассации — отрицательное число или будет автоматически конвертировано
    """
    # Получаем текущую открытую смену
    shift = session.exec(
        select(CashShift).where(CashShift.is_open == True).limit(1)
    ).first()
    if not shift:
        raise HTTPException(status_code=400, detail="Нет открытой смены. Откройте смену сначала.")
    
    tx_type = TransactionType(data.get("transaction_type", "income"))
    if tx_type == TransactionType.adjustment:
        raise HTTPException(status_code=400, detail="Корректировки запрещены")
    amount = data.get("amount", 0)

    # Для расхода и инкассации — проверяем достаточность баланса
    if tx_type in (TransactionType.expense, TransactionType.cashout):
        spend = abs(amount)
        txs = session.exec(
            select(CashTransaction).where(CashTransaction.shift_id == shift.id)
        ).all()
        current_income = sum(t.amount for t in txs if t.transaction_type == TransactionType.income)
        current_expense = sum(abs(t.amount) for t in txs if t.transaction_type in (TransactionType.expense, TransactionType.cashout))
        current_balance = shift.initial_amount + current_income - current_expense
        if spend > current_balance:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно средств в кассе. Текущий баланс: {current_balance:.2f}₽, запрошено: {spend:.2f}₽"
            )

    # Для расхода, возврата и инкассации делаем сумму отрицательной
    if tx_type in (TransactionType.expense, TransactionType.cashout, TransactionType.adjustment) and amount > 0:
        amount = -amount
    
    payment_method_str = data.get("payment_method", "cash")
    pm = PaymentMethod(payment_method_str) if payment_method_str in ("cash", "card") else PaymentMethod.cash

    tx = CashTransaction(
        shift_id=shift.id,
        order_id=data.get("order_id"),
        transaction_type=tx_type,
        payment_method=pm,
        amount=amount,
        comment=data.get("comment", ""),
        created_by=current_user.id,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    
    logger.info(f"Транзакция: {tx_type.value} {amount}₽ в смене #{shift.id}")
    
    # Авто-начисление ЗП если приход привязан к заказу с мастером
    if tx_type == TransactionType.income and tx.order_id and amount > 0:
        order = session.get(Order, tx.order_id)
        if order and order.master_id:
            salary_amount = round(amount * 0.4)
            salary_record = SalaryRecord(
                user_id=order.master_id,
                order_id=tx.order_id,
                calculated_amount=salary_amount,
                status="accrued",
                period_start=datetime.utcnow().replace(day=1),
                period_end=datetime.utcnow(),
                comment=f"Авто: приход #{tx.id}",
            )
            session.add(salary_record)
            session.commit()
    
    return {
        "id": tx.id,
        "transaction_type": tx.transaction_type.value,
        "amount": tx.amount,
        "comment": tx.comment,
        "created_at": tx.created_at.isoformat(),
    }


@router.get("/orders/ready", summary="Заказы готовые к выдаче")
def get_ready_orders(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Заказы со статусом 'ready' (готов к выдаче)"""
    orders = session.exec(
        select(Order).where(Order.status == "ready_pickup").order_by(Order.ready_at.desc())
    ).all()
    
    result = []
    for o in orders:
        result.append({
            "id": o.id,
            "client_name": o.client_name,
            "client_phone": o.client_phone,
            "device_model": f"{o.device_brand} {o.device_model}",
            "total_cost": o.total_cost,
            "ready_at": o.ready_at.isoformat() if o.ready_at else None,
            "master_username": o.master.username if o.master else None,
        })
    
    return result


@router.get("/shift/history", summary="История смен")
def get_shift_history(
    skip: int = Query(0),
    limit: int = Query(50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """История кассовых смен"""
    shifts = session.exec(
        select(CashShift).order_by(CashShift.opened_at.desc(), CashShift.id.desc()).offset(skip).limit(limit)
    ).all()
    
    result = []
    for s in shifts:
        balance = calculate_shift_balance(session, s)

        # Получаем имена пользователей
        opened_by_user = session.get(User, s.opened_by)
        closed_by_user = session.get(User, s.closed_by) if s.closed_by else None

        result.append({
            "id": s.id,
            "opened_at": s.opened_at.isoformat(),
            "closed_at": s.closed_at.isoformat() if s.closed_at else None,
            "opened_by": s.opened_by,
            "opened_by_username": opened_by_user.username if opened_by_user else None,
            "closed_by": s.closed_by,
            "closed_by_username": closed_by_user.username if closed_by_user else None,
            "initial_amount": s.initial_amount,
            "final_amount": balance["cash_balance"] if s.is_open else s.final_amount,
            "is_open": s.is_open,
            "income": balance["income"],
            "expense": balance["expense"],
            "cash_income": balance["cash_income"],
            "card_income": balance["card_income"],
            "current_balance": balance["current_balance"],
            "cash_balance": balance["cash_balance"],
            "transactions_count": balance["transactions_count"],
        })

    current_shift = session.exec(
        select(CashShift).where(CashShift.is_open == True).order_by(CashShift.opened_at.desc(), CashShift.id.desc()).limit(1)
    ).first()
    if current_shift:
        total_cash = calculate_shift_balance(session, current_shift)["cash_balance"]
    else:
        last_closed_shift = get_last_closed_shift(session)
        total_cash = last_closed_shift.final_amount if last_closed_shift else 0
    
    return {
        "shifts": result,
        "total_cash_in_cache": total_cash,
    }


@router.get("/monthly-summary", summary="Месячная статистика приходов")
def get_monthly_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Сумма ПРИХОДОВ за текущий календарный месяц.
    Возвращает: общий приход, возвраты, чистый приход.
    """
    today = datetime.utcnow()
    month_start = datetime(today.year, today.month, 1)
    month_label = today.strftime("%Y-%m")

    # Приход по заказам
    income = session.exec(
        select(CashTransaction).where(
            CashTransaction.transaction_type == TransactionType.income,
            CashTransaction.created_at >= month_start,
            CashTransaction.order_id.isnot(None),
        )
    ).all()

    cash_total = sum(t.amount for t in income if t.payment_method == PaymentMethod.cash)
    card_total = sum(t.amount for t in income if t.payment_method == PaymentMethod.card)
    grand_total = cash_total + card_total

    # Возвраты (expense с пометкой "возврат")
    refunds = session.exec(
        select(CashTransaction).where(
            CashTransaction.transaction_type != TransactionType.income,
            CashTransaction.created_at >= month_start,
            CashTransaction.order_id.isnot(None),
            CashTransaction.comment.ilike('%возврат%'),
        )
    ).all()
    refund_cash = sum(abs(t.amount) for t in refunds if t.payment_method == PaymentMethod.cash)
    refund_card = sum(abs(t.amount) for t in refunds if t.payment_method == PaymentMethod.card)
    refund_total = refund_cash + refund_card

    # Текущий остаток в кассе (последняя закрытая смена)
    last_shift = session.exec(
        select(CashShift).where(CashShift.is_open == False).order_by(CashShift.closed_at.desc())
    ).first()
    current_cash = last_shift.final_amount if last_shift else 0

    return {
        "month": month_label,
        "cash_total": round(cash_total, 2),
        "card_total": round(card_total, 2),
        "grand_total": round(grand_total, 2),
        "refund_cash": round(refund_cash, 2),
        "refund_card": round(refund_card, 2),
        "refund_total": round(refund_total, 2),
        "net_total": round(grand_total - refund_total, 2),
        "current_cash": round(current_cash, 2),
    }
