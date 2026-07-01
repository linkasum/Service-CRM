"""
API для графика работы сотрудников
"""
from datetime import date as date_type
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.work_schedule import WorkSchedule
from models.role import Role
from pydantic import BaseModel

router = APIRouter(prefix="/api/work-schedule", tags=["Расписание"])


class WorkScheduleCreate(BaseModel):
    user_id: int
    date: date_type


def _build_item(ws: WorkSchedule, user: Optional[User], role: Optional[Role]) -> dict:
    return {
        "id": ws.id,
        "user_id": ws.user_id,
        "date": str(ws.date),
        "user_name": user.full_name or user.username if user else None,
        "user_role": role.name if role else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


@router.get("", summary="График за месяц")
def get_schedule_by_month(
    month: str = Query(..., example="2026-04", description="Год и месяц в формате YYYY-MM"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Возвращает все записи за месяц (формат month=2026-04)"""
    try:
        year, m = map(int, month.split("-"))
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат месяца, ожидается YYYY-MM")

    from calendar import monthrange
    last_day = monthrange(year, m)[1]
    date_from = date_type(year, m, 1)
    date_to = date_type(year, m, last_day)

    schedules = session.exec(
        select(WorkSchedule).where(
            WorkSchedule.date >= date_from,
            WorkSchedule.date <= date_to,
        ).order_by(WorkSchedule.date, WorkSchedule.user_id)
    ).all()

    items = []
    for ws in schedules:
        user = session.get(User, ws.user_id)
        role = session.get(Role, user.role_id) if user and user.role_id else None
        items.append(_build_item(ws, user, role))

    return {"items": items}


@router.get("/by-date", summary="Кто работает в конкретный день")
def get_schedule_by_date(
    date: date_type = Query(..., example="2026-04-23"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Возвращает список сотрудников, работающих в указанный день"""
    schedules = session.exec(
        select(WorkSchedule).where(WorkSchedule.date == date)
    ).all()

    items = []
    for ws in schedules:
        user = session.get(User, ws.user_id)
        role = session.get(Role, user.role_id) if user and user.role_id else None
        items.append(_build_item(ws, user, role))

    return {"items": items}


@router.get("/users", summary="Список сотрудников для назначения в график")
def get_schedule_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Возвращает активных сотрудников для модального окна графика."""
    users = session.exec(
        select(User).where(User.is_active == True).order_by(User.full_name, User.username)
    ).all()

    items = []
    for user in users:
        role = session.get(Role, user.role_id) if user.role_id else None
        items.append({
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name or user.username,
            "role_name": role.name if role else None,
            "is_active": user.is_active,
        })

    return {"items": items}


@router.post("", summary="Добавить сотрудника на день", status_code=201)
def add_work_day(
    data: WorkScheduleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Поставить сотрудника в расписание на указанную дату. 409 если уже есть."""
    existing = session.exec(
        select(WorkSchedule).where(
            WorkSchedule.user_id == data.user_id,
            WorkSchedule.date == data.date,
        )
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Запись для этого сотрудника на эту дату уже существует")

    ws = WorkSchedule(
        user_id=data.user_id,
        date=data.date,
        created_by=current_user.id,
    )
    session.add(ws)
    session.commit()
    session.refresh(ws)

    user = session.get(User, ws.user_id)
    role = session.get(Role, user.role_id) if user and user.role_id else None
    return _build_item(ws, user, role)


@router.delete("/{schedule_id}", summary="Удалить запись из расписания")
def delete_work_day(
    schedule_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить запись о рабочем дне сотрудника"""
    ws = session.get(WorkSchedule, schedule_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Запись не найдена")

    session.delete(ws)
    session.commit()
    return {"ok": True, "id": schedule_id}
