"""
Orders маршруты: CRUD заказов, смена статуса, фильтрация
"""
import os
from typing import List, Optional
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, func
from sqlalchemy import text
from datetime import datetime, timedelta

from core.database import get_session
from core.config import get_settings
from core.security import get_current_user
from models.order import Order
from models.order_comment import OrderComment
from models.order_payment import OrderPayment
from models.order_payment import PaymentType
from models.cash_transaction import CashTransaction, TransactionType
from models.cash_shift import CashShift
from models.user import User
from models.role import Role
from models.notification_task import NotificationTask
from schemas.order import OrderCreate, OrderUpdate, OrderRead, OrderStatusChange
from core.logging import logger
from core.websocket_manager import ws_manager
from routes.clients import get_or_create_client

router = APIRouter(prefix="/api/orders", tags=["Заказы"])


STATUS_LABELS = {
    "new": "Новый",
    "diagnostics": "Диагностика",
    "agreed": "Согласован",
    "repair": "В работе",
    "waiting_parts": "Ожидает запчасти",
    "ready": "Готов",
    "ready_pickup": "На выдаче",
    "issued": "Выдан",
    "issued_br": "Выдан БР",
    "cancelled": "Отменён",
}


def _telegram_proxy_url() -> Optional[str]:
    return (
        os.getenv("TELEGRAM_BOT_PROXY_URL")
        or os.getenv("ALL_PROXY")
        or os.getenv("TELEGRAM_PROXY_URL")
        or os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
    )


async def _send_telegram_message(chat_id: int, text: str) -> None:
    token = get_settings().TELEGRAM_BOT_TOKEN
    if not token:
        return
    kwargs = {"timeout": 20.0}
    proxy_url = _telegram_proxy_url()
    if proxy_url:
        kwargs["proxy"] = proxy_url
        kwargs["trust_env"] = False
    async with httpx.AsyncClient(**kwargs) as client:
        await client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
        )


async def _notify_master_status_change(
    session: Session,
    order: Order,
    old_status: str,
    new_status: str,
    current_user: User,
) -> None:
    if not order.master_id or order.master_id == current_user.id:
        return
    master = session.get(User, order.master_id)
    if not master or not master.telegram_chat_id:
        return
    try:
        await _send_telegram_message(
            master.telegram_chat_id,
            "Статус вашего заказа изменен\n"
            f"Заказ #{order.id}: {order.device_model}\n"
            f"{STATUS_LABELS.get(old_status, old_status)} -> {STATUS_LABELS.get(new_status, new_status)}\n"
            f"Изменил: {current_user.full_name or current_user.username}",
        )
    except Exception as exc:
        logger.warning(f"Не удалось отправить Telegram-уведомление мастеру по заказу #{order.id}: {exc}")


async def _notify_client_order(session: Session, order: Order, event: str = "created") -> None:
    client_user = session.exec(
        select(User).where(User.phone == order.client_phone)
    ).first()
    if not client_user or not client_user.telegram_chat_id:
        return
    device = f"{order.device_brand or ''} {order.device_model}".strip()
    if event == "created":
        text = (
            f"Создан новый заказ #{order.id}\n"
            f"Устройство: {device}\n"
            f"Статус: {STATUS_LABELS.get(order.status, order.status)}"
        )
    elif event == "ready_pickup":
        text = (
            f"Ваш заказ #{order.id} готов к выдаче\n"
            f"Устройство: {device}\n"
            f"Стоимость: {order.total_cost or 0:,.0f} ₽".replace(",", " ")
        )
    elif event == "status":
        text = (
            f"Статус заказа #{order.id} изменен\n"
            f"Устройство: {device}\n"
            f"Новый статус: {STATUS_LABELS.get(order.status, order.status)}"
        )
    else:
        return
    try:
        await _send_telegram_message(client_user.telegram_chat_id, text)
    except Exception as exc:
        logger.warning(f"Не удалось отправить Telegram-уведомление клиенту по заказу #{order.id}: {exc}")


# === Маппинг полей в человекочитаемые названия ===
FIELD_LABELS = {
    "client_name": "Имя клиента",
    "client_phone": "Телефон",
    "client_email": "Email",
    "age_group": "Возрастная группа",
    "source": "Источник",
    "complaint": "Причина обращения",
    "device_category": "Вид устройства",
    "device_brand": "Бренд",
    "device_model": "Модель",
    "serial_number": "IMEI/SN",
    "accessories": "Комплектация",
    "has_delivery": "Доставка",
    "is_warranty": "По гарантии",
    "order_type": "Тип заказа",
    "master_id": "Мастер",
    "manager_id": "Менеджер",
    "total_cost": "Общая сумма",
    "parts_cost": "Стоимость запчастей",
    "work_cost": "Стоимость работ",
    "diagnostic_result": "Результат диагностики",
    "recommended_services": "Рекомендованные услуги",
    "warranty_days": "Гарантия (дни)",
    "notes": "Заметки",
}


def _create_change_comment(
    session: Session,
    order: Order,
    user: User,
    changed_fields: dict,
    action: str = "изменены",
):
    """Создать системный комментарий об изменении полей заказа"""
    if not changed_fields:
        return

    lines = []
    for field, value in changed_fields.items():
        label = FIELD_LABELS.get(field, field)
        old_val = value.get("old", "—")
        new_val = value.get("new", "—")
        # Для ID-полей (мастер/менеджер) покажем имя
        if field in ("master_id", "manager_id"):
            if new_val:
                new_user = session.get(User, new_val)
                new_val = new_user.username if new_user else f"#{new_val}"
            if old_val:
                old_user = session.get(User, old_val)
                old_val = old_user.username if old_user else f"#{old_val}"
        lines.append(f"{label}: «{old_val or 'пусто'}» → «{new_val or 'пусто'}»")

    text = f"📝 Заказ {action}. Изменения:\n" + "\n".join(lines)

    comment = OrderComment(
        order_id=order.id,
        user_id=user.id,
        username=user.username,
        role_name=user.role.name if user.role else "",
        text=text,
        is_system=True,
    )
    session.add(comment)


def _enrich_order(order: Order, session: Session) -> dict:
    """Добавить данные о мастере и приёмщике"""
    master_username = None
    acceptor_username = None
    manager_name = order.manager_name or None
    if order.master_id:
        master = session.get(User, order.master_id)
        master_username = (master.full_name or master.username) if master else None
    if order.acceptor_id:
        acceptor = session.get(User, order.acceptor_id)
        acceptor_username = (acceptor.full_name or acceptor.username) if acceptor else None
    if order.manager_id:
        mgr = session.get(User, order.manager_id)
        if mgr:
            manager_name = mgr.full_name or mgr.username
    result = order.model_dump()
    result["master_username"] = master_username
    result["acceptor_username"] = acceptor_username
    result["manager_name"] = manager_name
    
    # Запчасти
    result["parts"] = [
        {
            "id": op.id,
            "part_id": op.part_id,
            "part_name": op.part.name if op.part else None,
            "quantity": op.quantity,
            "price_at_order": op.price_at_order,
        }
        for op in order.parts
    ] if order.parts else []
    
    # Услуги
    result["service_items"] = [
        {
            "id": os_item.id,
            "service_id": os_item.service_id,
            "service_name": os_item.service_name,
            "quantity": os_item.quantity,
            "price_at_order": os_item.price_at_order,
            "comment": os_item.comment,
        }
        for os_item in order.service_items
    ] if order.service_items else []

    # Считаем стоимость запчастей и работ
    result["parts_cost"] = sum(op.price_at_order * op.quantity for op in order.parts) if order.parts else 0
    result["work_cost"] = sum(os_item.price_at_order * os_item.quantity for os_item in order.service_items) if order.service_items else 0
    result["total_cost"] = result["parts_cost"] + result["work_cost"]

    # Возвраты
    from models.order_payment import PaymentType
    refunds = session.exec(
        select(OrderPayment).where(
            OrderPayment.order_id == order.id,
            OrderPayment.payment_type == PaymentType.refund
        )
    ).all()
    result["refunds_amount"] = sum(abs(p.amount) for p in refunds) if refunds else 0

    return result


@router.get("/", summary="Список заказов")
def get_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    master_id: Optional[int] = Query(None),
    client_phone: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список заказов с фильтрацией и поиском"""
    try:
        query = select(Order)

        if status_filter:
            query = query.where(Order.status == status_filter)
        if master_id:
            query = query.where(Order.master_id == master_id)
        if client_phone:
            query = query.where(Order.client_phone == client_phone)
        if search:
            query = query.where(
                (Order.client_name.ilike(f"%{search}%")) |
                (Order.client_phone.ilike(f"%{search}%")) |
                (Order.device_model.ilike(f"%{search}%")) |
                (Order.device_brand.ilike(f"%{search}%"))
            )
        if current_user.role and current_user.role.name == 'master':
            query = query.where(Order.master_id == current_user.id)

        count_query = select(func.count(Order.id)).select_from(query.subquery())
        total = session.exec(count_query).one()

        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        orders = session.exec(query).all()

        result = [_enrich_order(order, session) for order in orders]
        return {"items": result, "total": total}
    except Exception as e:
        logger.error(f"Ошибка получения заказов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки заказов")


@router.get("/{order_id}", summary="Детали заказа")
def get_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить детали конкретного заказа"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    return _enrich_order(order, session)


@router.post("/", response_model=OrderRead, summary="Создать заказ")
def create_order(
    order_data: OrderCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать новый заказ. Клиент автоматически ищется в базе по телефону или создаётся"""
    try:
        # Ищем или создаём клиента в базе
        client = get_or_create_client(
            session=session,
            phone=order_data.client_phone,
            name=order_data.client_name,
            client_type=order_data.client_type or "individual",
            email=order_data.client_email,
            source=order_data.source,
            age_group=order_data.age_group,
        )

        # Создаём заказ
        order = Order.model_validate(order_data)
        order.status = "new"
        order.acceptor_id = current_user.id
        order.manager_name = current_user.full_name or current_user.username

        session.add(order)
        session.commit()
        session.refresh(order)

        # Системный комментарий о создании заказа
        create_comment = OrderComment(
            order_id=order.id,
            user_id=current_user.id,
            username=current_user.username,
            role_name=current_user.role.name if current_user.role else "",
            text=f"📋 Заказ создан. Клиент: {order.client_name} ({order.client_phone}), Устройство: {order.device_brand} {order.device_model}",
            is_system=True,
        )
        session.add(create_comment)
        session.commit()

        logger.info(f"Создан заказ #{order.id} пользователем {current_user.username}")

        try:
            from routes.notifications import add_notification
            add_notification(session, current_user.id, current_user.username,
                "order_created", f"Создан заказ #{order.id} - {order.client_name}", order.id)
        except Exception:
            pass

        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_notify_client_order(session, order, "created"))
        except RuntimeError:
            pass

        return _enrich_order(order, session)
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка создания заказа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания заказа")


@router.patch("/{order_id}", response_model=OrderRead, summary="Обновить заказ")
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить данные заказа с логированием всех изменений в комментарии"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        update_data = order_data.model_dump(exclude_unset=True)

        # Запоминаем старые значения для логирования
        changed_fields = {}
        for key, value in update_data.items():
            old_value = getattr(order, key, None)
            if old_value != value:
                changed_fields[key] = {"old": old_value, "new": value}

        # Применяем изменения
        for key, value in update_data.items():
            setattr(order, key, value)

        session.add(order)
        session.commit()
        session.refresh(order)

        # Логируем изменения в комментарий
        if changed_fields:
            # Определяем тип изменений для текста
            has_assignment = any(f in changed_fields for f in ("master_id", "manager_id"))
            has_finance = any(f in changed_fields for f in ("total_cost", "parts_cost", "work_cost"))

            if has_assignment:
                _create_change_comment(session, order, current_user, changed_fields, action="обновлён (назначение)")
            elif has_finance:
                _create_change_comment(session, order, current_user, changed_fields, action="обновлён (финансы)")
            else:
                _create_change_comment(session, order, current_user, changed_fields, action="обновлён")
            session.commit()

        logger.info(f"Обновлён заказ #{order.id} пользователем {current_user.username}")

        return _enrich_order(order, session)
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка обновления заказа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления заказа")


@router.patch("/{order_id}/status", response_model=OrderRead, summary="Сменить статус заказа")
async def change_status(
    order_id: int,
    status_data: OrderStatusChange,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сменить статус заказа"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    valid_statuses = [
        "new", "diagnostics", "agreed", "repair", "waiting_parts",
        "ready", "ready_pickup", "issued", "issued_br", "cancelled"
    ]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый статус. Допустимые: {', '.join(valid_statuses)}"
        )

    old_status = order.status
    if old_status in ("issued", "issued_br") and status_data.status not in ("issued", "issued_br"):
        raise HTTPException(
            status_code=400,
            detail="Заказ уже выдан. Смена статуса невозможна."
        )

    try:
        old_status = order.status
        order.status = status_data.status

        if status_data.status == "ready" and order.ready_at:
            notification = NotificationTask(
                order_id=order.id,
                client_phone=order.client_phone,
                message_text=f"Ваш заказ #{order.id} ({order.device_model}) готов к выдаче!",
                send_at=order.ready_at,
            )
            session.add(notification)
            logger.info(f"Создана задача уведомления для заказа #{order.id}")

        if status_data.status == "issued":
            order.issued_at = datetime.now()
            
            # Гарантия
            if order.warranty_days:
                order.warranty_until = datetime.now() + timedelta(days=order.warranty_days)
            
            # Создаём OrderPayment и CashTransaction ПЕРЕД начислением ЗП
            existing_payment = session.exec(
                select(OrderPayment).where(
                    OrderPayment.order_id == order.id,
                    OrderPayment.payment_type == PaymentType.final,
                )
            ).first()
            if not existing_payment and order.total_cost:
                from models.order_payment import PaymentMethod as PM, PaymentStatus as PS
                from models.cash_transaction import PaymentMethod as CTPM
                pm_str = getattr(status_data, 'payment_method', None) or 'cash'
                pm = PM(pm_str) if pm_str in ('cash', 'card', 'transfer') else PM.cash
                payment = OrderPayment(
                    order_id=order.id,
                    payment_type=PaymentType.final,
                    amount=order.total_cost,
                    method=pm,
                    status=PS.completed,
                    comment=f"Авто при выдаче заказа #{order.id}",
                    created_by_id=current_user.id,
                )
                session.add(payment)
                
                # CashTransaction в активной смене
                active_shift = session.exec(
                    select(CashShift).where(CashShift.is_open == True).limit(1)
                ).first()
                if active_shift:
                    ct = CashTransaction(
                        shift_id=active_shift.id,
                        order_id=order.id,
                        transaction_type=TransactionType.income,
                        amount=order.total_cost,
                        payment_method=CTPM(pm_str) if pm_str in ('cash', 'card') else CTPM.cash,
                        comment=f"Оплата заказа #{order.id}",
                        created_by=current_user.id,
                    )
                    session.add(ct)
                session.flush()  # важно: чтобы auto_assign_salary увидел транзакцию
            
            # Автоначисление зарплаты мастеру
            if order.master_id:
                from routes.salary_assignment import auto_assign_salary
                try:
                    salary_result = auto_assign_salary(
                        order_id=order.id,
                        session=session,
                        current_user=current_user,
                    )
                    if salary_result.get('already_accrued'):
                        logger.info(f"Зарплата за заказ #{order.id} уже начислена: {salary_result.get('salary_amount', 0)}₽")
                    else:
                        logger.info(f"Зарплата за заказ #{order.id}: {salary_result.get('salary_amount', 0)}₽")
                except Exception as e:
                    logger.error(f"Ошибка начисления зарплаты: {e}")

        session.add(order)
        session.commit()
        session.refresh(order)

        # Системный комментарий о смене статуса
        sys_comment = OrderComment(
            order_id=order_id,
            user_id=current_user.id,
            username=current_user.username,
            role_name=current_user.role.name if current_user.role else "",
            text=f"Статус изменён: {STATUS_LABELS.get(old_status, old_status)} → {STATUS_LABELS.get(order.status, order.status)}",
            is_system=True,
        )
        session.add(sys_comment)
        session.commit()

        # WebSocket уведомление о смене статуса
        order_data = _enrich_order(order, session)
        await ws_manager.broadcast({
            "type": "order_status_changed",
            "order_id": order.id,
            "old_status": old_status,
            "new_status": order.status,
            "order": order_data,
            "changed_by": current_user.username,
        })

        await _notify_master_status_change(session, order, old_status, order.status, current_user)

        if order.status == "ready_pickup":
            import asyncio
            asyncio.create_task(_notify_client_order(session, order, "ready_pickup"))
        else:
            import asyncio
            asyncio.create_task(_notify_client_order(session, order, "status"))

        logger.info(
            f"Статус заказа #{order.id} изменён: {old_status} -> {order.status} "
            f"пользователем {current_user.username}"
        )

        try:
            from routes.notifications import add_notification
            add_notification(session, current_user.id, current_user.username,
                "order_status_changed",
                f"Заказ #{order.id}: {STATUS_LABELS.get(old_status, old_status)} -> {STATUS_LABELS.get(order.status, order.status)}",
                order.id)
        except Exception:
            pass

        return _enrich_order(order, session)
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка смены статуса: {e}")
        raise HTTPException(status_code=500, detail="Ошибка смены статуса")


@router.delete("/{order_id}", summary="Удалить заказ")
def delete_order(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить заказ"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        for tbl in ["order_services", "order_parts", "order_payments",
                     "order_comments", "notification_tasks", "salary_records",
                     "documents"]:
            session.execute(text(f"DELETE FROM {tbl} WHERE order_id = :oid"), {"oid": order_id})
        session.delete(order)
        session.commit()

        logger.info(f"Удалён заказ #{order_id} пользователем {current_user.username}")

        return {"message": f"Заказ #{order_id} удалён"}
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка удаления заказа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления заказа")
