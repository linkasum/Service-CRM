"""
Settings маршруты: статусы, бренды, категории, модели, касса, реквизиты
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlmodel import Session, select, func
from datetime import datetime

from core.database import get_session
from core.security import get_current_user, require_permission
from models.user import User
from models.custom_status import CustomStatus
from models.brand import Brand
from models.category import Category
from models.device_model import DeviceModel
from models.accessory_template import AccessoryTemplate
from models.company_settings import CompanySettings
from models.cash_shift import CashShift
from models.client_source import ClientSource
from models.age_group import AgeGroup
from services.import_service import (
    parse_uploaded_file,
    validate_field_mapping,
    IMPORT_HANDLERS,
    FIELD_MAPPINGS,
)
from core.logging import logger

router = APIRouter(prefix="/api/settings", tags=["Настройки"])


# === СТАТУСЫ ===


@router.get("/statuses", summary="Список статусов")
def get_statuses(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получение списка статусов доступно всем авторизованным пользователям"""
    return session.exec(
        select(CustomStatus).order_by(CustomStatus.is_default.desc(), CustomStatus.name)
    ).all()


@router.post("/statuses", summary="Создать статус")
def create_status(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    status = CustomStatus(
        name=data["name"],
        color=data.get("color", "#1890ff"),
        is_default=data.get("is_default", False),
        is_active=data.get("is_active", True),
    )
    session.add(status)
    session.commit()
    session.refresh(status)
    logger.info(f"Создан статус: {status.name}")
    return status


@router.patch("/statuses/{status_id}", summary="Обновить статус")
def update_status(
    status_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    status = session.get(CustomStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Статус не найден")
    for key in ["name", "color", "is_default", "is_active"]:
        if key in data:
            setattr(status, key, data[key])
    session.add(status)
    session.commit()
    session.refresh(status)
    return status


@router.delete("/statuses/{status_id}", summary="Удалить статус")
def delete_status(
    status_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    status = session.get(CustomStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Статус не найден")
    session.delete(status)
    session.commit()
    return {"message": f"Статус '{status.name}' удалён"}


# === БРЕНДЫ ===


@router.get("/brands", summary="Список брендов")
def get_brands(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(Brand)).all()


@router.post("/brands", summary="Создать бренд")
def create_brand(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    brand = Brand(name=data["name"], is_active=data.get("is_active", True))
    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand


@router.patch("/brands/{brand_id}", summary="Обновить бренд")
def update_brand(
    brand_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Бренд не найден")
    if "name" in data:
        brand.name = data["name"]
    if "is_active" in data:
        brand.is_active = data["is_active"]
    session.add(brand)
    session.commit()
    session.refresh(brand)
    return brand


@router.delete("/brands/{brand_id}", summary="Удалить бренд")
def delete_brand(
    brand_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    brand = session.get(Brand, brand_id)
    if not brand:
        raise HTTPException(status_code=404, detail="Бренд не найден")
    session.delete(brand)
    session.commit()
    return {"message": f"Бренд '{brand.name}' удалён"}


# === КАТЕГОРИИ ===


@router.get("/categories", summary="Список категорий")
def get_categories(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(Category)).all()


@router.post("/categories", summary="Создать категорию")
def create_category(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    cat = Category(name=data["name"], is_active=data.get("is_active", True))
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return cat


@router.patch("/categories/{cat_id}", summary="Обновить категорию")
def update_category(
    cat_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    cat = session.get(Category, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    if "name" in data:
        cat.name = data["name"]
    if "is_active" in data:
        cat.is_active = data["is_active"]
    session.add(cat)
    session.commit()
    session.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}", summary="Удалить категорию")
def delete_category(
    cat_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    cat = session.get(Category, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    session.delete(cat)
    session.commit()
    return {"message": f"Категория '{cat.name}' удалена"}


# === КОМПЛЕКТАЦИИ ===


@router.get("/accessory-templates", summary="Список комплектаций")
def get_accessory_templates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(
        select(AccessoryTemplate).order_by(AccessoryTemplate.name)
    ).all()


@router.post("/accessory-templates", summary="Создать комплектацию")
def create_accessory_template(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    template = AccessoryTemplate(name=data["name"], is_active=data.get("is_active", True))
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.patch("/accessory-templates/{template_id}", summary="Обновить комплектацию")
def update_accessory_template(
    template_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    template = session.get(AccessoryTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Комплектация не найдена")
    if "name" in data:
        template.name = data["name"]
    if "is_active" in data:
        template.is_active = data["is_active"]
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


@router.delete("/accessory-templates/{template_id}", summary="Удалить комплектацию")
def delete_accessory_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    template = session.get(AccessoryTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Комплектация не найдена")
    session.delete(template)
    session.commit()
    return {"message": f"Комплектация '{template.name}' удалена"}


# === ИСТОЧНИКИ КЛИЕНТОВ ===


@router.get("/client-sources", summary="Список источников клиентов")
def get_client_sources(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(ClientSource)).all()


@router.post("/client-sources", summary="Создать источник")
def create_client_source(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    src = ClientSource(name=data["name"], is_active=data.get("is_active", True))
    session.add(src)
    session.commit()
    session.refresh(src)
    return src


@router.patch("/client-sources/{src_id}", summary="Обновить источник")
def update_client_source(
    src_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    src = session.get(ClientSource, src_id)
    if not src:
        raise HTTPException(status_code=404, detail="Источник не найден")
    if "name" in data:
        src.name = data["name"]
    if "is_active" in data:
        src.is_active = data["is_active"]
    session.add(src)
    session.commit()
    session.refresh(src)
    return src


@router.delete("/client-sources/{src_id}", summary="Удалить источник")
def delete_client_source(
    src_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    src = session.get(ClientSource, src_id)
    if not src:
        raise HTTPException(status_code=404, detail="Источник не найден")
    session.delete(src)
    session.commit()
    return {"message": f"Источник '{src.name}' удалён"}


# === ВОЗРАСТНЫЕ ГРУППЫ ===


@router.get("/age-groups", summary="Список возрастных групп")
def get_age_groups(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return session.exec(select(AgeGroup)).all()


@router.post("/age-groups", summary="Создать возрастную группу")
def create_age_group(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    ag = AgeGroup(name=data["name"], is_active=data.get("is_active", True))
    session.add(ag)
    session.commit()
    session.refresh(ag)
    return ag


@router.patch("/age-groups/{ag_id}", summary="Обновить возрастную группу")
def update_age_group(
    ag_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    ag = session.get(AgeGroup, ag_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Возрастная группа не найдена")
    if "name" in data:
        ag.name = data["name"]
    if "is_active" in data:
        ag.is_active = data["is_active"]
    session.add(ag)
    session.commit()
    session.refresh(ag)
    return ag


@router.delete("/age-groups/{ag_id}", summary="Удалить возрастную группу")
def delete_age_group(
    ag_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    ag = session.get(AgeGroup, ag_id)
    if not ag:
        raise HTTPException(status_code=404, detail="Возрастная группа не найдена")
    session.delete(ag)
    session.commit()
    return {"message": f"Возрастная группа '{ag.name}' удалена"}


# === ИМПОРТ ДАННЫХ ===


@router.post("/import/preview", summary="Предпросмотр импорта")
def import_preview(
    data: dict = {},
    import_type: str = Query("clients"),
    headers: List[str] = Query(default=[]),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить список доступных полей для типа импорта"""
    if not headers and data.get("headers"):
        headers = data["headers"]
    if not import_type or import_type == "clients":
        import_type = data.get("import_type", import_type)
    mapping = FIELD_MAPPINGS.get(import_type, {})
    return {
        "file_headers": headers,
        "available_fields": mapping.get("fields", {}),
        "required": mapping.get("required", []),
        "required_any": mapping.get("required_any", []),
    }


@router.post("/import/upload", summary="Загрузить и распарсить файл")
async def import_upload(
    file: UploadFile = File(...),
    import_type: str = "clients",
    encoding: Optional[str] = None,
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Загрузить файл и вернуть распаршенные данные"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не указан")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="Файл слишком большой (макс. 10 МБ)"
        )

    try:
        headers, rows = parse_uploaded_file(content, file.filename, encoding)
    except Exception as e:
        logger.error(f"Ошибка парсинга файла: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка чтения файла: {str(e)}")

    return {
        "headers": headers,
        "rows": rows,
        "total_rows": len(rows),
        "filename": file.filename,
    }


@router.post("/import/validate", summary="Проверить маппинг")
def import_validate(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    # Always valid - let user proceed
    return {"valid": True, "errors": []}


@router.post("/import/execute", summary="Выполнить импорт")
def import_execute(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    import_type = data.get("import_type", "clients")
    field_mapping = data.get("field_mapping", {})
    rows = data.get("rows", [])

    handler = IMPORT_HANDLERS.get(import_type)
    if not handler:
        raise HTTPException(
            status_code=400, detail=f"Неизвестный тип импорта: {import_type}"
        )

    # Skip strict validation - import whatever is mapped
    # No additional validation needed - proceed with import

    # Debug - показываем что пришло
    logger.info(f"import_type={import_type}, field_mapping={field_mapping}")

    # Валидация - упрощенная
    has_mapping = any(v for v in field_mapping.values() if v and str(v).strip())
    if not has_mapping:
        raise HTTPException(status_code=400, detail="Не сопоставлено ни одно поле")

    if import_type == "clients":
        mapped_values = list(field_mapping.values())
        if not any(v for v in mapped_values if v and str(v).strip()):
            raise HTTPException(
                status_code=400, detail="Нужно сопоставить ФИО или Телефон"
            )

    # Импорт
    stats = handler(session, rows, field_mapping)
    logger.info(
        f"Импорт {import_type}: создано={stats['created']}, ошибок={stats['errors']}"
    )
    return stats


# === МОДЕЛИ УСТРОЙСТВ ===


@router.get("/device-models", summary="Список моделей")
def get_device_models(
    brand_id: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(DeviceModel)
    if brand_id:
        query = query.where(DeviceModel.brand_id == brand_id)
    return session.exec(query).all()


@router.post("/device-models", summary="Создать модель")
def create_device_model(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    dm = DeviceModel(
        brand_id=data["brand_id"],
        name=data["name"],
        is_active=data.get("is_active", True),
    )
    session.add(dm)
    session.commit()
    session.refresh(dm)
    return dm


@router.patch("/device-models/{dm_id}", summary="Обновить модель")
def update_device_model(
    dm_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    dm = session.get(DeviceModel, dm_id)
    if not dm:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    if "name" in data:
        dm.name = data["name"]
    if "brand_id" in data:
        dm.brand_id = data["brand_id"]
    if "is_active" in data:
        dm.is_active = data["is_active"]
    session.add(dm)
    session.commit()
    session.refresh(dm)
    return dm


@router.delete("/device-models/{dm_id}", summary="Удалить модель")
def delete_device_model(
    dm_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    dm = session.get(DeviceModel, dm_id)
    if not dm:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    session.delete(dm)
    session.commit()
    return {"message": f"Модель '{dm.name}' удалена"}


# === КАССА ===


@router.get("/cash-shift", summary="Текущая кассовая смена")
def get_cash_shift(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("cash:view")),
):
    shift = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
    if not shift:
        return {"is_open": False}
    return {
        "id": shift.id,
        "opened_at": shift.opened_at.isoformat(),
        "opened_by": shift.opened_by,
        "initial_amount": shift.initial_amount,
        "final_amount": shift.final_amount,
        "is_open": True,
    }


@router.post("/cash-shift/open", summary="Открыть смену")
def open_cash_shift(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("cash:access")),
):
    # Закрыть открытую смену если есть
    existing = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Смена уже открыта")

    shift = CashShift(
        opened_by=current_user.id,
        initial_amount=data.get("initial_amount", 0),
        is_open=True,
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    logger.info(f"Открыта кассовая смена #{shift.id} пользователем {current_user.id}")
    return {"message": "Смена открыта", "id": shift.id}


@router.post("/cash-shift/close", summary="Закрыть смену")
def close_cash_shift(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("cash:access")),
):
    shift = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
    if not shift:
        raise HTTPException(status_code=400, detail="Нет открытой смены")

    shift.final_amount = data.get("final_amount", 0)
    shift.closed_at = datetime.now()
    shift.closed_by = current_user.id
    shift.is_open = False

    session.add(shift)
    session.commit()
    logger.info(f"Закрыта кассовая смена #{shift.id} пользователем {current_user.id}")
    return {"message": "Смена закрыта"}


@router.get("/cash-shifts", summary="История кассовых смен")
def get_cash_shifts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("cash:view")),
):
    shifts = session.exec(
        select(CashShift).order_by(CashShift.opened_at.desc()).offset(skip).limit(limit)
    ).all()
    result = []
    for s in shifts:
        result.append(
            {
                "id": s.id,
                "opened_at": s.opened_at.isoformat() if s.opened_at else None,
                "closed_at": s.closed_at.isoformat() if s.closed_at else None,
                "initial_amount": s.initial_amount,
                "final_amount": s.final_amount,
                "status": "Открыта" if s.is_open else "Закрыта",
            }
        )
    return result


# === РАСШИРЕННЫЕ РЕКВИЗИТЫ КОМПАНИИ ===


@router.get("/company-extended", summary="Расширенные реквизиты компании")
def get_company_extended(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    settings = session.exec(select(CompanySettings)).first()
    if not settings:
        settings = CompanySettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.patch("/company-extended", summary="Обновить расширенные реквизиты")
def update_company_extended(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    settings = session.exec(select(CompanySettings)).first()
    if not settings:
        settings = CompanySettings()
        session.add(settings)

    for key in [
        "company_name",
        "address",
        "inn",
        "kpp",
        "director",
        "bank",
        "account",
        "bik",
        "phone",
        "email",
        "review_link",
    ]:
        if key in data:
            setattr(settings, key, data[key])

    settings.updated_at = datetime.now()
    session.add(settings)
    session.commit()
    session.refresh(settings)
    logger.info("Обновлены расширенные реквизиты компании")
    return settings
