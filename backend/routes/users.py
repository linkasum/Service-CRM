"""
Users маршруты: управление сотрудниками
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from core.database import get_session
from core.security import get_current_user, get_password_hash, require_permission
from models.user import User
from models.role import Role
from models.order import Order
from models.salary_config import SalaryConfig
from core.logging import logger

router = APIRouter(prefix="/api/users", tags=["Сотрудники"])


def normalize_telegram_chat_id(value) -> Optional[int]:
    """Accept empty form values as unlinking Telegram."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Telegram ID должен быть числом")


def ensure_telegram_chat_id_available(
    session: Session,
    telegram_chat_id: Optional[int],
    current_user_id: Optional[int] = None,
) -> None:
    if telegram_chat_id is None:
        return

    existing = session.exec(
        select(User).where(User.telegram_chat_id == telegram_chat_id)
    ).first()
    if existing and existing.id != current_user_id:
        raise HTTPException(
            status_code=400,
            detail=f"Telegram ID уже привязан к сотруднику {existing.username}",
        )


@router.get("/", summary="Список сотрудников")
def get_users(
    is_active: Optional[bool] = Query(None),
    role_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список всех сотрудников"""
    query = select(User)

    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if role_id:
        query = query.where(User.role_id == role_id)

    users = session.exec(query.offset(skip).limit(limit)).all()

    result = []
    for u in users:
        role = session.get(Role, u.role_id) if u.role_id else None
        # Подсчёт заказов
        order_count = session.exec(
            select(func.count(Order.id)).where(
                (Order.master_id == u.id) | (Order.acceptor_id == u.id)
            )
        ).one()

        total_cost = session.exec(
            select(func.coalesce(func.sum(Order.total_cost), 0)).where(
                (Order.master_id == u.id) | (Order.acceptor_id == u.id)
            )
        ).one()

        # Получаем формулу зарплаты сотрудника
        salary_cfg = None
        if u.salary_config_id:
            salary_cfg = session.get(SalaryConfig, u.salary_config_id)

        result.append({
            "id": u.id,
            "username": u.username,
            "full_name": u.full_name or u.username,
            "role_id": u.role_id,
            "role_name": role.name if role else None,
            "telegram_chat_id": u.telegram_chat_id,
            "email": u.email,
            "phone": u.phone,
            "salary_config_id": u.salary_config_id,
            "salary_config_name": salary_cfg.description if salary_cfg else None,
            "salary_formula": salary_cfg.formula_string if salary_cfg else None,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "order_count": order_count,
            "total_cost": float(total_cost),
        })

    return {"items": result, "total": len(result)}


@router.post("/", summary="Создать сотрудника")
def create_user(
    user_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Создать нового сотрудника"""
    username = user_data.get("username")
    full_name = user_data.get("full_name")
    email = user_data.get("email") or None
    phone = user_data.get("phone") or None
    password = user_data.get("password")
    role_id = user_data.get("role_id")
    salary_config_id = user_data.get("salary_config_id")
    telegram_chat_id = normalize_telegram_chat_id(user_data.get("telegram_chat_id"))
    is_active = user_data.get("is_active", True)

    if not username or not password:
        raise HTTPException(status_code=400, detail="Логин и пароль обязательны")

    existing = session.exec(select(User).where(User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Пользователь с таким логином уже существует")

    if role_id:
        role = session.get(Role, role_id)
        if not role:
            raise HTTPException(status_code=400, detail="Роль не найдена")

    if salary_config_id:
        cfg = session.get(SalaryConfig, salary_config_id)
        if not cfg:
            raise HTTPException(status_code=400, detail="Формула зарплаты не найдена")

    ensure_telegram_chat_id_available(session, telegram_chat_id)

    user = User(
        username=username,
        full_name=full_name or username,
        email=email,
        phone=phone,
        password_hash=get_password_hash(password),
        role_id=role_id,
        salary_config_id=salary_config_id,
        telegram_chat_id=telegram_chat_id,
        is_active=is_active,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    role = session.get(Role, user.role_id) if user.role_id else None
    logger.info(f"Создан сотрудник {user.username}")

    return {
        "id": user.id,
        "username": user.username,
        "role_id": user.role_id,
        "salary_config_id": user.salary_config_id,
        "telegram_chat_id": user.telegram_chat_id,
    }


@router.patch("/{user_id}", summary="Обновить сотрудника")
def update_user(
    user_id: int,
    user_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Обновить данные сотрудника"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    if "username" in user_data:
        new_username = user_data["username"].strip()
        if new_username:
            # Проверка уникальности
            existing = session.exec(select(User).where(User.username == new_username, User.id != user_id)).first()
            if existing:
                raise HTTPException(status_code=400, detail="Этот логин уже занят")
            user.username = new_username

    if "full_name" in user_data:
        user.full_name = user_data["full_name"] or None

    if "email" in user_data:
        user.email = user_data["email"] or None

    if "phone" in user_data:
        user.phone = user_data["phone"] or None

    if "is_active" in user_data:
        user.is_active = user_data["is_active"]

    if "role_id" in user_data:
        role_id = user_data["role_id"]
        if role_id:
            role = session.get(Role, role_id)
            if not role:
                raise HTTPException(status_code=400, detail="Роль не найдена")
        user.role_id = role_id

    if "salary_config_id" in user_data:
        cfg_id = user_data["salary_config_id"]
        if cfg_id:
            cfg = session.get(SalaryConfig, cfg_id)
            if not cfg:
                raise HTTPException(status_code=400, detail="Формула зарплаты не найдена")
        user.salary_config_id = cfg_id

    if "telegram_chat_id" in user_data:
        telegram_chat_id = normalize_telegram_chat_id(user_data["telegram_chat_id"])
        ensure_telegram_chat_id_available(session, telegram_chat_id, user_id)
        user.telegram_chat_id = telegram_chat_id

    if "password" in user_data and user_data["password"]:
        user.password_hash = get_password_hash(user_data["password"])

    session.add(user)
    session.commit()
    session.refresh(user)

    role = session.get(Role, user.role_id) if user.role_id else None
    logger.info(f"Обновлён сотрудник {user.username}")

    return {
        "id": user.id,
        "username": user.username,
        "role_id": user.role_id,
        "salary_config_id": user.salary_config_id,
        "telegram_chat_id": user.telegram_chat_id,
    }


@router.delete("/{user_id}", summary="Деактивировать сотрудника")
def deactivate_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Деактивировать сотрудника (не удалять)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя деактивировать себя")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    user.is_active = False
    session.add(user)
    session.commit()

    logger.info(f"Деактивирован сотрудник {user.username}")
    return {"message": f"Сотрудник {user.username} деактивирован"}


@router.delete("/{user_id}/hard", summary="Удалить сотрудника навсегда")
def hard_delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Полностью удалить сотрудника из базы"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить себя")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    # Проверяем есть ли заказы за этим мастером
    orders = session.exec(select(Order).where(Order.master_id == user_id)).all()
    
    if orders:
        # Переназначаем заказы на первого доступного мастера с той же ролью
        other_master = session.exec(
            select(User).where(
                User.role_id == user.role_id,
                User.id != user_id,
                User.is_active == True
            )
        ).first()
        
        if other_master:
            for order in orders:
                order.master_id = other_master.id
                session.add(order)
            logger.info(f"Заказы ({len(orders)}) переназначены на {other_master.username}")
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Нельзя удалить: есть заказы ({len(orders)}), а других мастеров нет"
            )
    
    # Удаляем записи о зарплате
    from models.salary_record import SalaryRecord
    salary_records = session.exec(select(SalaryRecord).where(SalaryRecord.user_id == user_id)).all()
    for sr in salary_records:
        session.delete(sr)
    logger.info(f"Удалено записей о зарплате: {len(salary_records)}")
    
    # Теперь удаляем пользователя
    session.delete(user)
    session.commit()

    logger.info(f"Удалён сотрудник {user.username} (ID={user_id})")
    return {"message": f"Сотрудник {user.username} удалён навсегда"}


@router.post("/{user_id}/reset-password", summary="Сбросить пароль")
def reset_password(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("users:manage")),
):
    """Сбросить пароль сотрудника на временный"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    import random
    import string
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user.password_hash = get_password_hash(temp_password)
    session.add(user)
    session.commit()

    logger.info(f"Сброшен пароль сотрудника {user.username}")
    return {"message": "Пароль сброшен", "temporary_password": temp_password}
