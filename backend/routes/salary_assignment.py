"""
Маршруты: Автоматическое начисление зарплаты мастеру
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timedelta

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.salary_config import SalaryConfig, SalaryType
from models.salary_record import SalaryRecord
from core.logging import logger

router = APIRouter(prefix="/api/salary/assignment", tags=["Начисление зарплаты"])


@router.post("/auto-assign/{order_id}", summary="Автоначисление зарплаты при выдаче")
def auto_assign_salary(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Автоматически начислить зарплату мастеру при выдаче заказа.
    Вызывается при смене статуса на 'issued' через кассу.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    if not order.master_id:
        return {"message": "Мастер не назначен, зарплата не начислена", "salary_amount": 0}
    
    # Получаем формулу зарплаты мастера
    master = session.get(User, order.master_id)
    config = None
    
    # 1. Сначала ищем личную формулу мастера
    if master and master.salary_config_id:
        config = session.get(SalaryConfig, master.salary_config_id)
    
    # 2. Если нет - берём АКТИВНУЮ формулу типа formula (для мастеров)
    #    Приоритет у formula потому что это процент от работ
    if not config:
        formula_configs = session.exec(
            select(SalaryConfig).where(
                SalaryConfig.config_type == SalaryType.formula,
                SalaryConfig.is_active == True,
            )
        ).all()
        if formula_configs:
            config = formula_configs[0]  # Берём первую активную formula
    
    # 3. Если нет formula - берём первую активную (любого типа)
    if not config:
        config = session.exec(
            select(SalaryConfig).where(SalaryConfig.is_active == True)
        ).first()
    
    if not config:
        return {"message": "Нет активной формулы зарплаты", "salary_amount": 0}

    # ПРОВЕРКА: Не начислена ли уже зарплата за этот заказ
    from models.salary_record import SalaryRecord
    existing_salary = session.exec(
        select(SalaryRecord).where(
            SalaryRecord.order_id == order_id,
            SalaryRecord.user_id == order.master_id,
            SalaryRecord.status == 'accrued'
        )
    ).first()
    
    if existing_salary:
        logger.info(f"Зарплата за заказ #{order_id} уже начислена ({existing_salary.calculated_amount}₽)")
        return {
            "message": f"Зарплата уже начислена: {existing_salary.calculated_amount}₽",
            "salary_amount": existing_salary.calculated_amount,
            "already_accrued": True,
        }

    # Рассчитываем зарплату
    salary_amount = 0
    total_cost = order.total_cost or 0
    parts_cost = order.parts_cost or 0
    
    # Считаем cash_net/card_net для заказа из реальных транзакций
    from models.cash_transaction import CashTransaction
    cash_net = 0.0
    card_net = 0.0
    txs = session.exec(
        select(CashTransaction).where(CashTransaction.order_id == order_id)
    ).all()
    for tx in txs:
        amt = tx.amount or 0
        pm = (tx.payment_method or '').lower()
        if pm == 'card':
            card_net += amt
        else:
            cash_net += amt
    
    payments_net = cash_net + card_net
    
    if config.config_type == SalaryType.fixed:
        # Фиксированная сумма
        salary_amount = config.fixed_amount or 0
    else:
        # Формула
        formula = config.formula_string or "0"
        formula = formula.replace("{cash_net}", str(cash_net))
        formula = formula.replace("{card_net}", str(card_net))
        formula = formula.replace("{payments_net}", str(payments_net))
        formula = formula.replace("{total_cost}", str(total_cost))
        formula = formula.replace("{parts_cost}", str(parts_cost))
        formula = formula.replace("{total}", str(total_cost))
        formula = formula.replace("{parts}", str(parts_cost))
        formula = formula.replace("total_cost", str(total_cost))
        formula = formula.replace("parts_cost", str(parts_cost))
        formula = formula.replace("total", str(total_cost))
        formula = formula.replace("parts", str(parts_cost))
        formula = formula.replace("{orders_count}", "1")
        formula = formula.replace("{base_salary}", str(config.fixed_amount or 0))
        
        import re
        try:
            sanitized = re.sub(r'[^0-9+\-*/().%\s]', '', formula)
            salary_amount = round(eval(sanitized))
        except Exception as e:
            logger.error(f"Ошибка расчёта зарплаты: {e}")
            salary_amount = 0
    
    # Создаём запись о начислении
    now = datetime.utcnow()
    pay_start = datetime(now.year, now.month, 1) if now.day <= 15 else datetime(now.year, now.month, 16)
    pay_end = datetime(now.year, now.month, 15, 23, 59, 59) if now.day <= 15 else (
        datetime(now.year, now.month + 1, 1) - timedelta(seconds=1) if now.month < 12 else datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
    )
    record = SalaryRecord(
        user_id=order.master_id,
        order_id=order_id,
        calculated_amount=salary_amount,
        period_start=pay_start,
        period_end=pay_end,
        status="accrued",
        comment=f"Автоначисление за заказ #{order_id}",
    )
    session.add(record)
    session.commit()

    # Системный комментарий в заказе
    from models.order_comment import OrderComment
    master_name = master.full_name or master.username if master else f"мастер #{order.master_id}"
    salary_comment = OrderComment(
        order_id=order_id,
        user_id=current_user.id,
        username=current_user.username,
        role_name=current_user.role.name if current_user.role else "",
        text=f"💰 Начислена зарплата {master_name}: {salary_amount}₽ (формула: {config.name or config.formula_string})",
        is_system=True,
    )
    session.add(salary_comment)
    session.commit()

    logger.info(f"Начислена зарплата {salary_amount}₽ мастеру #{order.master_id} за заказ #{order_id}")

    return {
        "message": f"Зарплата начислена: {salary_amount}₽",
        "salary_amount": salary_amount,
        "config_name": config.name or config.formula_string,
        "master_id": order.master_id,
        "master_username": master.username if master else None,
    }


@router.post("/recalculate/{order_id}", summary="Пересчитать зарплату для заказа")
def recalculate_salary(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Пересчитать и начислить зарплату мастеру для заказа.
    Можно вызывать повторно — создаст новую запись если зарплата ещё не начислена.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    if not order.master_id:
        return {"message": "Мастер не назначен, зарплата не начислена", "salary_amount": 0}

    # Проверяем была ли уже начислена зарплата
    existing_salary = session.exec(
        select(SalaryRecord).where(
            SalaryRecord.order_id == order_id,
            SalaryRecord.status == "accrued"
        )
    ).first()

    if existing_salary:
        return {
            "message": f"Зарплата уже начислена: {existing_salary.calculated_amount}₽",
            "salary_amount": existing_salary.calculated_amount,
            "record_id": existing_salary.id,
        }

    # Вызываем автоначисление
    return auto_assign_salary(order_id, session, current_user)
