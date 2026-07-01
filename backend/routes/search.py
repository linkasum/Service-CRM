"""
Маршруты: Унифицированный глобальный поиск
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, or_, func
import re

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.order import Order
from models.part import Part
from models.service import Service
from core.logging import logger

router = APIRouter(prefix="/api/search", tags=["Поиск"])


def _is_order_id(q: str) -> int | None:
    q = q.strip().lstrip("#")
    try:
        return int(q)
    except ValueError:
        return None


def _is_phone(q: str) -> str | None:
    digits = re.sub(r"\D", "", q)
    if len(digits) >= 10:
        return digits
    return None


@router.get("/", summary="Унифицированный глобальный поиск")
def global_search(
    q: str = Query(..., description="Поисковый запрос"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    q_lower = f"%{q.lower()}%"
    results = {"orders": [], "clients": [], "parts": [], "services": [], "total": 0}

    # Прямой поиск по номеру заказа
    order_id = _is_order_id(q)
    if order_id:
        order = session.get(Order, order_id)
        if order:
            results["orders"].append({
                "id": order.id, "client": order.client_name,
                "phone": order.client_phone,
                "device": f"{order.device_brand} {order.device_model}".strip(),
                "status": order.status, "total_cost": order.total_cost,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "type": "order",
            })

    # Поиск по телефону — точный
    phone = _is_phone(q)
    if phone:
        phone_orders = session.exec(
            select(Order)
            .where(Order.client_phone.contains(phone[-10:]))
            .order_by(Order.created_at.desc())
            .limit(20)
        ).all()
        for o in phone_orders:
            if o.id not in {r["id"] for r in results["orders"]}:
                results["orders"].append({
                    "id": o.id, "client": o.client_name,
                    "phone": o.client_phone,
                    "device": f"{o.device_brand} {o.device_model}".strip(),
                    "status": o.status, "total_cost": o.total_cost,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                    "type": "order",
                })

    # Общий поиск по тексту
    text_orders = session.exec(
        select(Order)
        .where(
            or_(
                Order.client_name.ilike(q_lower),
                Order.client_phone.ilike(q_lower),
                Order.device_model.ilike(q_lower),
                Order.device_brand.ilike(q_lower),
                Order.serial_number.ilike(q_lower),
                Order.complaint.ilike(q_lower),
            )
        )
        .order_by(Order.created_at.desc())
        .limit(15)
    ).all()

    seen_ids = {r["id"] for r in results["orders"]}
    for o in text_orders:
        if o.id not in seen_ids:
            results["orders"].append({
                "id": o.id, "client": o.client_name,
                "phone": o.client_phone,
                "device": f"{o.device_brand} {o.device_model}".strip(),
                "status": o.status, "total_cost": o.total_cost,
                "created_at": o.created_at.isoformat() if o.created_at else None,
                "type": "order",
            })
            seen_ids.add(o.id)

    # Клиенты (группировка по телефону)
    phones_seen = set()
    all_orders_for_clients = session.exec(
        select(Order).where(
            or_(Order.client_name.ilike(q_lower), Order.client_phone.ilike(q_lower))
        ).order_by(Order.created_at.desc()).limit(30)
    ).all()
    for o in all_orders_for_clients:
        phone_key = o.client_phone.strip()
        if phone_key not in phones_seen:
            phones_seen.add(phone_key)
            results["clients"].append({
                "name": o.client_name, "phone": o.client_phone,
                "last_device": o.device_model,
                "last_order_id": o.id,
            })

    # Запчасти
    parts = session.exec(
        select(Part).where(Part.name.ilike(q_lower) | Part.article.ilike(q_lower)).limit(5)
    ).all()
    for p in parts:
        results["parts"].append({
            "id": p.id, "name": p.name, "article": p.article,
            "quantity": p.quantity, "sale_price": p.sale_price, "type": "part",
        })

    # Услуги
    services = session.exec(
        select(Service).where(Service.name.ilike(q_lower)).limit(5)
    ).all()
    for s in services:
        results["services"].append({
            "id": s.id, "name": s.name, "price": s.price,
            "status": s.status.value if hasattr(s.status, "value") else str(s.status),
            "type": "service",
        })

    results["total"] = len(results["orders"]) + len(results["clients"]) + len(results["parts"]) + len(results["services"])
    return results
