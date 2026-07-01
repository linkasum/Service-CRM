"""
Clients маршруты: база клиентов, история ремонтов
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.order import Order
from models.client import Client
from models.user import User
from schemas.notification import ClientRead, ClientFilter, ClientListResponse
from core.logging import logger

router = APIRouter(prefix="/api/clients", tags=["Клиенты"])


@router.get("/", response_model=ClientListResponse, summary="Список клиентов")
def get_clients(
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список клиентов из таблицы clients"""

    # Считаем общее количество
    count_query = select(func.count(Client.id))
    if search:
        count_query = count_query.where(
            (Client.name.ilike(f"%{search}%")) | (Client.phone.ilike(f"%{search}%"))
        )
    total = session.exec(count_query).one()

    # Выбираем клиентов
    query = select(Client)
    if search:
        query = query.where(
            (Client.name.ilike(f"%{search}%")) | (Client.phone.ilike(f"%{search}%"))
        )

    query = query.offset(skip).limit(limit).order_by(Client.id.desc())
    clients_db = session.exec(query).all()

    # Для каждого клиента считаем заказы
    clients = []
    for c in clients_db:
        orders_count = session.exec(
            select(func.count(Order.id)).where(Order.client_phone == c.phone)
        ).one()
        last_order = session.exec(
            select(Order)
            .where(Order.client_phone == c.phone)
            .order_by(Order.created_at.desc())
            .limit(1)
        ).first()

        clients.append(
            ClientRead(
                id=c.id,
                name=c.name,
                phone=c.phone,
                client_type=c.client_type,
                total_orders=orders_count,
                last_order_date=last_order.created_at if last_order else None,
            )
        )

    return {"clients": clients, "total": total}


@router.get("/{client_phone}", summary="Детали клиента и история заказов")
def get_client(
    client_phone: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить информацию о клиенте и историю его заказов"""
    client = session.exec(select(Client).where(Client.phone == client_phone)).first()

    orders = session.exec(
        select(Order)
        .where(Order.client_phone == client_phone)
        .order_by(Order.created_at.desc())
    ).all()

    if not orders and not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Если клиента нет в таблице - создаём из заказа
    if not client and orders:
        client = Client(
            name=orders[0].client_name,
            phone=client_phone,
            client_type=orders[0].client_type,
            email=orders[0].client_email,
        )
        session.add(client)
        session.commit()

    return {
        "name": client.name if client else (orders[0].client_name if orders else ""),
        "phone": client.phone if client else client_phone,
        "client_type": client.client_type if client else (orders[0].client_type if orders else "individual"),
        "email": client.email if client else (orders[0].client_email if orders else ""),
        "total_orders": len(orders),
        "orders": orders,
    }


@router.get("/search/by-phone", summary="Поиск клиента по телефону")
def search_client_by_phone(
    phone: str = Query(..., description="Телефон для поиска"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Найти клиента по телефону в таблице clients"""
    # Нормализуем телефон для поиска
    normalized_phone = phone.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    
    # Ищем точное совпадение или частичное
    client = session.exec(
        select(Client).where(
            Client.phone.ilike(f"%{normalized_phone}%") |
            Client.phone.ilike(f"%{phone}%")
        )
    ).first()
    
    if not client:
        return {"found": False}
    
    return {
        "found": True,
        "id": client.id,
        "name": client.name,
        "phone": client.phone,
        "email": client.email,
        "client_type": client.client_type,
        "source": client.source,
        "age_group": client.age_group,
    }


@router.get("/{client_phone}/info", summary="Информация о клиенте для заказа")
def get_client_info(
    client_phone: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить информацию о клиенте для отображения в заказе"""
    # Нормализуем телефон для поиска
    normalized_phone = client_phone.replace(" ", "").replace("-", "").replace("+", "").replace("(", "").replace(")", "")
    
    # Ищем клиента
    client = session.exec(
        select(Client).where(
            Client.phone.ilike(f"%{normalized_phone}%") |
            Client.phone.ilike(f"%{client_phone}%")
        )
    ).first()
    
    if not client:
        # Если клиент не найден в таблице clients, ищем в заказах
        orders = session.exec(
            select(Order).where(Order.client_phone == client_phone)
        ).all()
        
        if orders:
            # Возвращаем заглушку
            return {
                "name": orders[0].client_name,
                "phone": client_phone,
                "total_orders": len(orders),
                "loyalty": "Новый",
                "loyalty_color": "#1890ff",
                "avg_check": 0,
                "total_revenue": sum(o.total_cost or 0 for o in orders),
                "by_status": {},
                "devices": list(set(o.device_model for o in orders if o.device_model)),
                "orders": [],
            }
        return {
            "name": "Клиент не найден",
            "phone": client_phone,
            "total_orders": 0,
        }
    
    # Считаем статистику по заказам клиента
    orders = session.exec(
        select(Order).where(Order.client_phone == client.phone)
    ).all()
    
    # Статусы
    by_status = {}
    for o in orders:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    
    # Устройства
    devices = list(set(o.device_model for o in orders if o.device_model))
    
    # Лояльность
    total_orders = len(orders)
    if total_orders >= 10:
        loyalty = "VIP"
        loyalty_color = "#faad14"
    elif total_orders >= 5:
        loyalty = "Постоянный"
        loyalty_color = "#52c41a"
    elif total_orders >= 3:
        loyalty = "Знакомый"
        loyalty_color = "#1890ff"
    else:
        loyalty = "Новый"
        loyalty_color = "#d9d9d9"
    
    # Средняя сумма
    total_revenue = sum(o.total_cost or 0 for o in orders)
    avg_check = total_revenue / total_orders if total_orders > 0 else 0
    
    return {
        "name": client.name,
        "phone": client.phone,
        "email": client.email,
        "client_type": client.client_type,
        "total_orders": total_orders,
        "loyalty": loyalty,
        "loyalty_color": loyalty_color,
        "avg_check": avg_check,
        "total_revenue": total_revenue,
        "by_status": by_status,
        "devices": devices,
        "orders": orders[:20],  # Последние 20 заказов
    }


# Функция для автоматического поиска/создания клиента при создании заказа
def get_or_create_client(
    session: Session,
    phone: str,
    name: str,
    client_type: str = "individual",
    email: str = None,
    source: str = None,
    age_group: str = None,
):
    """Найти или создать клиента"""
    client = session.exec(select(Client).where(Client.phone == phone)).first()

    if not client:
        client = Client(
            name=name or "Клиент",
            phone=phone,
            client_type=client_type,
            email=email,
            source=source,
            age_group=age_group,
            created_at=datetime.now().isoformat(),
        )
        session.add(client)
        session.commit()
        session.refresh(client)

    return client
