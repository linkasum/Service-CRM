"""
Reports маршруты: расширенная аналитика и отчёты
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from core.database import get_session
from core.security import get_current_user
from models.order import Order
from models.user import User
from models.role import Role
from models.part import Part
from models.salary_record import SalaryRecord
from models.order_payment import OrderPayment
from core.logging import logger
from collections import defaultdict

router = APIRouter(prefix="/api/reports", tags=["Отчёты"])


def _parse_date_range(
    date_from: Optional[str],
    date_to: Optional[str],
) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Парсинг диапазона дат:
    - YYYY-MM-DD для date_from -> начало дня
    - YYYY-MM-DD для date_to   -> конец дня (включительно)
    - ISO datetime остаётся как есть
    """
    try:
        parsed_from = datetime.fromisoformat(date_from) if date_from else None
        parsed_to = datetime.fromisoformat(date_to) if date_to else None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Неверный формат даты, ожидается YYYY-MM-DD или ISO datetime") from exc

    if date_from and len(date_from) == 10 and parsed_from:
        parsed_from = parsed_from.replace(hour=0, minute=0, second=0, microsecond=0)
    if date_to and len(date_to) == 10 and parsed_to:
        parsed_to = parsed_to.replace(hour=23, minute=59, second=59, microsecond=999999)

    return parsed_from, parsed_to


@router.get("/orders-analytics", summary="Аналитика заказов")
def orders_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Аналитика заказов по статусам, мастерам, датам"""
    date_from_dt, date_to_dt = _parse_date_range(date_from, date_to)

    query = select(Order)
    if date_from_dt:
        query = query.where(Order.created_at >= date_from_dt)
    if date_to_dt:
        query = query.where(Order.created_at <= date_to_dt)

    orders = session.exec(query).all()

    # По статусам
    by_status = defaultdict(int)
    for o in orders:
        by_status[o.status] += 1

    # По мастерам
    by_master = defaultdict(lambda: {"count": 0, "revenue": 0})
    for o in orders:
        if o.master_id:
            master = session.get(User, o.master_id)
            name = master.username if master else "Не назначен"
            by_master[name]["count"] += 1
            by_master[name]["revenue"] += o.total_cost or 0

    # По дням (последние 30 дней)
    by_day = defaultdict(int)
    for o in orders:
        by_day[o.created_at.strftime("%Y-%m-%d")] += 1

    # Среднее время выполнения
    durations = []
    for o in orders:
        if o.issued_at and o.created_at:
            diff = (o.issued_at - o.created_at).days
            if diff > 0:
                durations.append(diff)

    return {
        "total_orders": len(orders),
        "by_status": dict(by_status),
        "by_master": dict(by_master),
        "by_day": dict(by_day),
        "avg_completion_days": round(sum(durations) / len(durations), 1) if durations else 0,
    }


@router.get("/financial", summary="Финансовый отчёт")
def financial_report(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Доходы, расходы, прибыль"""
    date_from_dt, date_to_dt = _parse_date_range(date_from, date_to)

    query = select(Order).where(Order.status == "issued")
    if date_from_dt:
        query = query.where(Order.created_at >= date_from_dt)
    if date_to_dt:
        query = query.where(Order.created_at <= date_to_dt)

    orders = session.exec(query).all()

    # Возвраты
    from models.order_payment import PaymentType
    refunds_query = select(OrderPayment).where(OrderPayment.payment_type == PaymentType.refund)
    if date_from_dt:
        refunds_query = refunds_query.where(OrderPayment.created_at >= date_from_dt)
    if date_to_dt:
        refunds_query = refunds_query.where(OrderPayment.created_at <= date_to_dt)
    refunds = session.exec(refunds_query).all()
    total_refunds = sum(abs(p.amount) for p in refunds)

    total_revenue = sum(o.total_cost or 0 for o in orders)
    total_parts_cost = sum(o.parts_cost or 0 for o in orders)
    total_work_cost = sum(o.work_cost or 0 for o in orders)
    gross_profit = total_revenue - total_parts_cost
    net_profit = gross_profit - total_refunds  # Чистая прибыль с учётом возвратов

    # Зарплатные выплаты
    salary_query = select(SalaryRecord)
    if date_from_dt:
        salary_query = salary_query.where(SalaryRecord.period_start >= date_from_dt)
    if date_to_dt:
        salary_query = salary_query.where(SalaryRecord.period_end <= date_to_dt)
    salary_records = session.exec(salary_query).all()
    total_salary = sum(r.calculated_amount for r in salary_records)

    # Доход по дням
    by_day = defaultdict(lambda: {"revenue": 0, "parts": 0, "profit": 0, "refunds": 0})
    for o in orders:
        day = o.created_at.strftime("%Y-%m-%d")
        by_day[day]["revenue"] += o.total_cost or 0
        by_day[day]["parts"] += o.parts_cost or 0
        by_day[day]["profit"] += (o.total_cost or 0) - (o.parts_cost or 0)
    
    # Возвраты по дням
    for r in refunds:
        if r.order_id:
            order = session.get(Order, r.order_id)
            if order:
                day = r.created_at.strftime("%Y-%m-%d")
                by_day[day]["refunds"] += abs(r.amount)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_parts_cost": round(total_parts_cost, 2),
        "total_work_cost": round(total_work_cost, 2),
        "total_refunds": round(total_refunds, 2),  # Сумма возвратов
        "gross_profit": round(gross_profit, 2),
        "net_profit": round(net_profit, 2),  # С учётом возвратов
        "total_salary": round(total_salary, 2),
        "orders_count": len(orders),
        "avg_order_value": round(total_revenue / len(orders), 2) if orders else 0,
        "by_day": dict(by_day),
    }


@router.get("/employees", summary="Отчёт по сотрудникам")
def employees_report(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Эффективность мастеров и менеджеров"""
    date_from_dt, date_to_dt = _parse_date_range(date_from, date_to)

    query = select(Order)
    if date_from_dt:
        query = query.where(Order.created_at >= date_from_dt)
    if date_to_dt:
        query = query.where(Order.created_at <= date_to_dt)
    orders = session.exec(query).all()

    # Мастера
    masters = defaultdict(lambda: {"completed": 0, "in_progress": 0, "revenue": 0, "avg_time": 0})
    for o in orders:
        if o.master_id:
            master = session.get(User, o.master_id)
            name = master.username if master else "Не назначен"
            if o.status == "issued":
                masters[name]["completed"] += 1
                masters[name]["revenue"] += o.total_cost or 0
            else:
                masters[name]["in_progress"] += 1

    # Менеджеры/приёмщики
    managers = defaultdict(lambda: {"processed": 0, "revenue": 0})
    for o in orders:
        if o.acceptor_id:
            acceptor = session.get(User, o.acceptor_id)
            name = acceptor.username if acceptor else "Не назначен"
            managers[name]["processed"] += 1
            managers[name]["revenue"] += o.total_cost or 0

    return {
        "masters": dict(masters),
        "managers": dict(managers),
    }


@router.get("/clients-analytics", summary="Аналитика клиентов")
def clients_analytics(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Демография и источники клиентов"""
    orders = session.exec(select(Order)).all()

    by_source = defaultdict(int)
    repeat_clients = defaultdict(int)
    unique_clients = set()

    for o in orders:
        if o.client_phone:
            unique_clients.add(o.client_phone)
            repeat_clients[o.client_phone] += 1
        if hasattr(o, 'source') and o.source:
            by_source[o.source] += 1

    repeat_count = sum(1 for c in repeat_clients.values() if c > 1)

    # Топ клиенты по количеству заказов
    top_clients = sorted(repeat_clients.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "unique_clients": len(unique_clients),
        "repeat_clients": repeat_count,
        "by_source": dict(by_source),
        "top_clients": [{"phone": p, "orders": c} for p, c in top_clients],
    }


@router.get("/devices-analytics", summary="Аналитика устройств")
def devices_analytics(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """По категориям, брендам и моделям с выручкой"""
    orders = session.exec(select(Order)).all()

    by_category: dict[str, dict] = {}
    by_brand: dict[str, dict] = {}
    by_model = defaultdict(int)

    for o in orders:
        cat = (o.device_category or '').strip()
        if cat and cat.lower() != 'phone':
            cat_name = cat
        elif cat.lower() == 'phone':
            cat_name = 'Телефон'
        else:
            cat_name = 'Не указано'

        if cat_name not in by_category:
            by_category[cat_name] = {"count": 0, "revenue": 0.0}
        by_category[cat_name]["count"] += 1
        by_category[cat_name]["revenue"] += o.total_cost or 0

        brand = (o.device_brand or '').strip() or 'Не указан'
        if brand not in by_brand:
            by_brand[brand] = {"count": 0, "revenue": 0.0}
        by_brand[brand]["count"] += 1
        by_brand[brand]["revenue"] += o.total_cost or 0

        if o.device_model:
            by_model[o.device_model] += 1

    return {
        "by_category": {k: v for k, v in sorted(by_category.items(), key=lambda x: x[1]["count"], reverse=True)},
        "by_brand": {k: v for k, v in sorted(by_brand.items(), key=lambda x: x[1]["count"], reverse=True)},
        "top_models": sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:10],
    }


@router.get("/warranty", summary="Гарантийный отчёт")
def warranty_report(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Анализ гарантийных заказов"""
    now = datetime.now()

    all_warranty = session.exec(
        select(Order).where(Order.is_warranty == True).order_by(Order.created_at.desc())
    ).all()

    active = [o for o in all_warranty if o.warranty_until and o.warranty_until > now]
    expired = [o for o in all_warranty if o.warranty_until and o.warranty_until <= now]

    return {
        "total": len(all_warranty),
        "active_warranty": len(active),
        "expired_warranty": len(expired),
        "orders": [
            {
                "id": o.id,
                "client": o.client_name,
                "device": f"{o.device_brand or ''} {o.device_model or ''}".strip(),
                "status": o.status,
                "warranty_days": o.warranty_days or 0,
                "warranty_until": o.warranty_until.isoformat() if o.warranty_until else None,
                "days_left": (o.warranty_until - now).days if o.warranty_until else 0,
                "total_cost": o.total_cost,
            }
            for o in all_warranty
        ],
    }


@router.get("/time-analytics", summary="Временная аналитика")
def time_analytics(
    period: str = Query("month", description="day, week, month, year"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Динамика по дням/неделям/месяцам + средний срок ремонта"""
    date_from_dt, date_to_dt = _parse_date_range(date_from, date_to)

    query = select(Order)
    if date_from_dt:
        query = query.where(Order.created_at >= date_from_dt)
    if date_to_dt:
        query = query.where(Order.created_at <= date_to_dt)
    orders = session.exec(query).all()

    # Средний срок ремонта: issued_at - created_at для выданных заказов
    issued = [o for o in orders if o.status == "issued" and o.created_at and o.issued_at]
    repair_times = [(o.issued_at - o.created_at).total_seconds() / 3600 for o in issued]  # часы

    avg_repair_hours = sum(repair_times) / len(repair_times) if repair_times else 0

    # По мастерам
    master_times = defaultdict(list)
    for o in issued:
        if o.master_id:
            master_times[o.master_id].append((o.issued_at - o.created_at).total_seconds() / 3600)

    masters_avg = []
    for mid, times in master_times.items():
        master = session.get(User, mid)
        name = (master.full_name or master.username) if master else f"ID {mid}"
        masters_avg.append({
            "master_id": mid,
            "master_name": name,
            "orders": len(times),
            "avg_hours": round(sum(times) / len(times), 1),
            "avg_days": round(sum(times) / len(times) / 24, 1),
        })
    masters_avg.sort(key=lambda x: x["orders"], reverse=True)

    # По периодам
    by_period = defaultdict(lambda: {"orders": 0, "revenue": 0, "issued": 0, "repair_hours": []})
    for o in orders:
        if period == "day":
            key = o.created_at.strftime("%Y-%m-%d")
        elif period == "week":
            key = f"{o.created_at.isocalendar()[0]}-W{o.created_at.isocalendar()[1]:02d}"
        elif period == "month":
            key = o.created_at.strftime("%Y-%m")
        else:
            key = o.created_at.strftime("%Y")

        by_period[key]["orders"] += 1
        by_period[key]["revenue"] += o.total_cost or 0
        if o.status == "issued":
            by_period[key]["issued"] += 1
        if o.status == "issued" and o.created_at and o.issued_at:
            by_period[key]["repair_hours"].append((o.issued_at - o.created_at).total_seconds() / 3600)

    sorted_data = sorted(by_period.items(), key=lambda x: x[0])
    chart_data = []
    for k, v in sorted_data:
        avg_h = sum(v["repair_hours"]) / len(v["repair_hours"]) if v["repair_hours"] else 0
        chart_data.append({
            "date": k,
            "orders": v["orders"],
            "revenue": round(v["revenue"], 2),
            "issued": v["issued"],
            "avg_repair_days": round(avg_h / 24, 1),
        })

    return {
        "period": period,
        "avg_repair_hours": round(avg_repair_hours, 1),
        "avg_repair_days": round(avg_repair_hours / 24, 1),
        "total_issued": len(issued),
        "masters_avg": masters_avg,
        "data": chart_data,
    }


@router.get("/dashboard-summary", summary="Сводный дашборд")
def dashboard_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Общая статистика и ключевые метрики"""
    date_from_dt, date_to_dt = _parse_date_range(date_from, date_to)

    query = select(Order)
    if date_from_dt:
        query = query.where(Order.created_at >= date_from_dt)
    if date_to_dt:
        query = query.where(Order.created_at <= date_to_dt)

    orders = session.exec(query).all()
    total = len(orders)

    issued_orders = [o for o in orders if o.status == "issued"]
    # Считаем реальный приход по транзакциям (только доходы, без расходов на запчасти)
    revenue = 0.0
    if issued_orders:
        oids = [o.id for o in issued_orders]
        from models.cash_transaction import CashTransaction, TransactionType as CTType
        income_sum = session.exec(
            select(func.sum(CashTransaction.amount)).where(
                CashTransaction.order_id.in_(oids),
                CashTransaction.transaction_type == CTType.income
            )
        ).first()
        # Вычитаем только возвраты (expense с комментарием "возврат")
        refund_sum = session.exec(
            select(func.sum(CashTransaction.amount)).where(
                CashTransaction.order_id.in_(oids),
                CashTransaction.transaction_type != CTType.income,
                CashTransaction.comment.ilike('%возврат%')
            )
        ).first()
        revenue = (income_sum or 0) + (refund_sum or 0)

    # Статусы
    by_status = defaultdict(int)
    for o in orders:
        by_status[o.status] += 1

    # Просроченные
    now = datetime.now()
    overdue = sum(1 for o in orders if o.ready_at and o.ready_at < now and o.status not in ("issued", "cancelled"))

    # На гарантии
    warranty_orders = sum(1 for o in orders if o.status == "issued" and o.warranty_until and o.warranty_until > now)

    # Мастера
    masters_data = defaultdict(lambda: {"master_id": 0, "master_name": "", "orders_completed": 0, "revenue": 0})
    for o in issued_orders:
        if o.master_id:
            master = session.get(User, o.master_id)
            name = master.username if master else "Не назначен"
            masters_data[name]["master_id"] = o.master_id
            masters_data[name]["master_name"] = name
            masters_data[name]["orders_completed"] += 1
            masters_data[name]["revenue"] += o.total_cost or 0

    # Запчасти на складе
    parts = session.exec(select(Part)).all()
    total_parts = sum(p.quantity for p in parts)
    parts_value = sum(p.quantity * p.sale_price for p in parts)

    # Статистика по дням
    by_day_orders = defaultdict(int)
    by_day_revenue = defaultdict(float)
    for o in orders:
        day = o.created_at.strftime("%Y-%m-%d")
        by_day_orders[day] += 1
    for o in issued_orders:
        day = o.created_at.strftime("%Y-%m-%d")
        by_day_revenue[day] += o.total_cost or 0

    # Генерируем полный ряд дат в запрошенном диапазоне
    if date_from_dt and date_to_dt:
        start_date = date_from_dt
        end_date = date_to_dt
    else:
        # По умолчанию — текущий месяц
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = now

    daily_orders = []
    daily_revenue = []
    current_date = start_date
    while current_date.date() <= end_date.date():
        day_key = current_date.strftime("%Y-%m-%d")
        label = current_date.strftime("%d.%m")
        daily_orders.append({"date": label, "count": by_day_orders.get(day_key, 0)})
        daily_revenue.append({"date": label, "amount": round(by_day_revenue.get(day_key, 0.0), 2)})
        current_date += timedelta(days=1)

    return {
        "total_orders": total,
        "issued_orders": len(issued_orders),
        "total_revenue": round(revenue, 2),
        "avg_order_value": round(revenue / len(issued_orders), 2) if issued_orders else 0,
        "by_status": dict(by_status),
        "status_breakdown": dict(by_status),  # Алиас для DashboardPage
        "overdue_orders": overdue,
        "warranty_orders": warranty_orders,
        "masters_efficiency": list(masters_data.values()),  # Для DashboardPage
        "active_masters": len(masters_data),
        "total_parts": total_parts,
        "parts_value": round(parts_value, 2),
        "daily_orders": daily_orders,
        "daily_revenue": daily_revenue,
    }


# Алиас для обратной совместимости (DashboardPage использует /dashboard)
@router.get("/dashboard", summary="Дашборд (алиас)")
def dashboard_alias(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return dashboard_summary(date_from, date_to, session, current_user)


@router.get("/marketing", summary="Маркетинговая аналитика")
def marketing_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    base = select(Order)
    if date_from:
        try: base = base.where(Order.created_at >= datetime.fromisoformat(date_from))
        except ValueError: pass
    if date_to:
        try: base = base.where(Order.created_at <= datetime.fromisoformat(date_to))
        except ValueError: pass

    orders = session.exec(base).all()

    age_stats: dict[str, dict] = {}
    source_stats: dict[str, dict] = {}
    total_revenue = sum(o.total_cost or 0 for o in orders)
    total_orders = len(orders)

    for o in orders:
        age = o.age_group or "Не указан"
        if age not in age_stats:
            age_stats[age] = {"count": 0, "revenue": 0.0}
        age_stats[age]["count"] += 1
        age_stats[age]["revenue"] += o.total_cost or 0

        src = o.source or "Не указан"
        if src not in source_stats:
            source_stats[src] = {"count": 0, "revenue": 0.0}
        source_stats[src]["count"] += 1
        source_stats[src]["revenue"] += o.total_cost or 0

    def format_group(name: str, data: dict) -> dict:
        return {
            "name": name,
            "count": data["count"],
            "revenue": round(data["revenue"], 2),
            "avg_check": round(data["revenue"] / data["count"], 2) if data["count"] else 0,
            "share_pct": round(data["count"] / total_orders * 100, 1) if total_orders else 0,
        }

    age_result = sorted(
        [format_group(k, v) for k, v in age_stats.items()],
        key=lambda x: x["count"], reverse=True,
    )
    source_result = sorted(
        [format_group(k, v) for k, v in source_stats.items()],
        key=lambda x: x["count"], reverse=True,
    )

    return {
        "age_groups": age_result,
        "sources": source_result,
        "total_orders": total_orders,
        "total_revenue": round(total_revenue, 2),
    }
