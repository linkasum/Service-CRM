"""
API для настроек рабочего времени
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.working_hours import WorkingHours
from schemas.working_hours import WorkingHoursCreate, WorkingHoursUpdate, WorkingHoursRead

router = APIRouter(prefix="/api/settings/working-hours", tags=["Настройки рабочего времени"])


@router.get("", summary="Список рабочих дней")
def get_working_hours(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить настройки рабочего времени"""
    return session.exec(select(WorkingHours).order_by(WorkingHours.day_of_week)).all()


@router.post("", summary="Создать/обновить рабочий день")
def create_or_update_working_hours(
    data: WorkingHoursCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать или обновить настройки рабочего дня"""
    # Проверяем есть ли уже такой день
    existing = session.exec(
        select(WorkingHours).where(WorkingHours.day_of_week == data.day_of_week)
    ).first()
    
    if existing:
        # Обновляем
        existing.day_name = data.day_name
        existing.is_working_day = data.is_working_day
        existing.start_time = data.start_time
        existing.end_time = data.end_time
        existing.lunch_start = data.lunch_start
        existing.lunch_end = data.lunch_end
        existing.description = data.description
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Создаём
        wh = WorkingHours(**data.dict())
        session.add(wh)
        session.commit()
        session.refresh(wh)
        return wh


@router.patch("/{day_id}", summary="Обновить рабочий день")
def update_working_hours(
    day_id: int,
    data: WorkingHoursUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить настройки рабочего дня"""
    wh = session.get(WorkingHours, day_id)
    if not wh:
        raise HTTPException(status_code=404, detail="День не найден")
    
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(wh, key, value)
    
    session.add(wh)
    session.commit()
    session.refresh(wh)
    return wh


@router.get("/schedule", summary="Текущее расписание")
def get_current_schedule(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Получить текущее расписание с расчётом рабочих часов.
    Возвращает: рабочие дни, часы в день, часы в неделю.
    """
    from datetime import datetime
    
    days = session.exec(select(WorkingHours).order_by(WorkingHours.day_of_week)).all()
    
    result = []
    total_hours = 0
    
    for day in days:
        if day.is_working_day:
            # Считаем часы
            start_h, start_m = map(int, day.start_time.split(':'))
            end_h, end_m = map(int, day.end_time.split(':'))
            hours = (end_h + end_m/60) - (start_h + start_m/60)
            
            # Вычитаем обед если есть
            if day.lunch_start and day.lunch_end:
                lunch_start_h, lunch_start_m = map(int, day.lunch_start.split(':'))
                lunch_end_h, lunch_end_m = map(int, day.lunch_end.split(':'))
                lunch_hours = (lunch_end_h + lunch_end_m/60) - (lunch_start_h + lunch_start_m/60)
                hours -= lunch_hours
            
            hours = round(hours, 2)
            total_hours += hours
            
            result.append({
                "day": day.day_name,
                "start": day.start_time,
                "end": day.end_time,
                "lunch": f"{day.lunch_start}-{day.lunch_end}" if day.lunch_start else None,
                "hours": hours,
            })
    
    return {
        "schedule": result,
        "total_hours_per_week": total_hours,
        "work_days_count": len(result),
    }
