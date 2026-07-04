"""
Settings маршруты: роли, настройки компании, шаблоны документов
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlmodel import Session, select

from core.database import get_session
from core.security import get_current_user, require_permission
from models.role import Role
from models.company_settings import CompanySettings
from models.document_template import DocumentTemplate
from models.user import User
from models.document_template_assignment import DocumentTemplateAssignment
from schemas.role import RoleCreate, RoleUpdate, RoleRead
from schemas.notification import (
    CompanySettingsUpdate, CompanySettingsRead,
    DocumentTemplateCreate, DocumentTemplateUpdate, DocumentTemplateRead,
)
from core.logging import logger

router = APIRouter(prefix="/api/settings", tags=["Настройки"])


class OrderNumberingUpdate(BaseModel):
    next_order_number: int = Field(..., ge=1)


def _get_order_sequence_state(session: Session) -> dict:
    """Return current order id sequence state without advancing the sequence."""
    sequence_name = session.exec(
        text("SELECT pg_get_serial_sequence('orders', 'id')")
    ).one()[0]
    if not sequence_name:
        raise HTTPException(status_code=500, detail="Sequence заказов не найдена")

    max_order_id = session.exec(text("SELECT COALESCE(MAX(id), 0) FROM orders")).one()[0]
    sequence_state = session.exec(
        text(f"SELECT last_value, is_called FROM {sequence_name}")
    ).one()
    last_value = int(sequence_state[0])
    is_called = bool(sequence_state[1])
    next_order_number = last_value + 1 if is_called else last_value

    return {
        "sequence_name": sequence_name,
        "last_value": last_value,
        "is_called": is_called,
        "max_order_id": int(max_order_id),
        "next_order_number": int(next_order_number),
        "min_allowed_next_order_number": int(max_order_id) + 1,
    }


# === Нумерация заказов ===

@router.get("/order-numbering", summary="Текущая нумерация заказов")
def get_order_numbering(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Получить следующий номер заказа и минимально допустимое значение."""
    return _get_order_sequence_state(session)


@router.patch("/order-numbering", summary="Установить следующий номер заказа")
def update_order_numbering(
    data: OrderNumberingUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Установить следующий номер заказа через PostgreSQL sequence."""
    state = _get_order_sequence_state(session)
    min_allowed = state["min_allowed_next_order_number"]
    if data.next_order_number < min_allowed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Нельзя установить номер ниже {min_allowed}: "
                f"в базе уже есть заказ #{state['max_order_id']}"
            ),
        )

    session.exec(
        text("SELECT setval(CAST(:sequence_name AS regclass), :next_order_number, false)"),
        params={
            "sequence_name": state["sequence_name"],
            "next_order_number": data.next_order_number,
        },
    )
    session.commit()

    logger.info(
        "Следующий номер заказа установлен на %s пользователем %s",
        data.next_order_number,
        current_user.username,
    )
    return _get_order_sequence_state(session)


# === Роли ===

@router.get("/roles", response_model=List[RoleRead], summary="Список ролей")
def get_roles(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    """Получить список всех ролей"""
    return session.exec(select(Role)).all()


@router.post("/roles", response_model=RoleRead, summary="Создать роль")
def create_role(
    role_data: RoleCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    """Создать новую роль с правами"""
    existing = session.exec(select(Role).where(Role.name == role_data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Роль с таким именем уже существует")
    
    role = Role.model_validate(role_data)
    session.add(role)
    session.commit()
    session.refresh(role)
    
    logger.info(f"Создана роль: {role.name}")
    return role


@router.patch("/roles/{role_id}", response_model=RoleRead, summary="Обновить роль")
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    """Обновить роль и её права"""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    update_data = role_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    
    session.add(role)
    session.commit()
    session.refresh(role)
    
    return role


@router.delete("/roles/{role_id}", summary="Удалить роль")
def delete_role(
    role_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    """Удалить роль (если нет пользователей с этой ролью)"""
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    # Проверка что нет пользователей с этой ролью
    users_with_role = session.exec(select(User).where(User.role_id == role_id)).all()
    if users_with_role:
        raise HTTPException(
            status_code=400,
            detail=f"Невозможно удалить: есть {len(users_with_role)} пользователей с этой ролью"
        )
    
    session.delete(role)
    session.commit()
    
    logger.info(f"Удалена роль: {role.name}")
    return {"message": f"Роль '{role.name}' удалена"}


# === Настройки компании ===

@router.get("/company", response_model=CompanySettingsRead, summary="Настройки компании")
def get_company_settings(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить настройки компании"""
    settings = session.exec(select(CompanySettings)).first()
    if not settings:
        settings = CompanySettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return settings


@router.patch("/company", response_model=CompanySettingsRead, summary="Обновить настройки компании")
def update_company_settings(
    settings_data: CompanySettingsUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("settings.manage")),
):
    """Обновить настройки компании (реквизиты)"""
    settings = session.exec(select(CompanySettings)).first()
    if not settings:
        settings = CompanySettings()
        session.add(settings)
    
    update_data = settings_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    
    from datetime import datetime
    settings.updated_at = datetime.now()
    
    session.add(settings)
    session.commit()
    session.refresh(settings)
    
    logger.info("Обновлены настройки компании")
    return settings


# === Шаблоны документов ===

@router.get("/templates", response_model=List[DocumentTemplateRead], summary="Шаблоны документов")
def get_templates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить все шаблоны документов"""
    return session.exec(select(DocumentTemplate)).all()


@router.post("/templates", response_model=DocumentTemplateRead, summary="Создать шаблон")
def create_template(
    template_data: DocumentTemplateCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Создать новый шаблон документа"""
    from datetime import datetime
    template = DocumentTemplate(
        type=template_data.type,
        content_template=template_data.content_template,
        updated_at=datetime.now()
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    logger.info(f"Создан шаблон: {template.type}")
    return template


@router.get("/templates/{template_type}", response_model=DocumentTemplateRead, summary="Шаблон по типу")
def get_template(
    template_type: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить шаблон документа по типу"""
    template = session.exec(
        select(DocumentTemplate).where(DocumentTemplate.type == template_type)
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return template


@router.patch("/templates/{template_type}", response_model=DocumentTemplateRead, summary="Обновить шаблон")
def update_template(
    template_type: str,
    template_data: DocumentTemplateUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить шаблон документа"""
    template = session.exec(
        select(DocumentTemplate).where(DocumentTemplate.type == template_type)
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    if template_data.content_template is not None:
        template.content_template = template_data.content_template
    
    from datetime import datetime
    template.updated_at = datetime.now()
    
    session.add(template)
    session.commit()
    session.refresh(template)
    
    logger.info(f"Обновлён шаблон: {template_type}")
    return template


# === Назначения шаблонов ===

@router.get("/template-assignments", response_model=List[dict], summary="Назначения шаблонов")
def get_template_assignments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить все назначения шаблонов на типы документов"""
    from sqlmodel import and_
    assignments = session.exec(
        select(DocumentTemplateAssignment).where(DocumentTemplateAssignment.is_active == True)
    ).all()
    
    result = []
    for a in assignments:
        template = session.get(DocumentTemplate, a.template_id)
        result.append({
            "id": a.id,
            "document_type": a.document_type,
            "template_id": a.template_id,
            "template_name": template.content_template[:50] if template else None,
            "template_type": template.type if template else None,
        })
    
    return result


@router.post("/template-assignments", response_model=dict, summary="Назначить шаблон")
def assign_template(
    assignment_data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Назначить шаблон на тип документа"""
    from datetime import datetime
    
    document_type = assignment_data.get("document_type")
    template_id = assignment_data.get("template_id")
    
    if not document_type or not template_id:
        raise HTTPException(status_code=400, detail="document_type и template_id обязательны")
    
    # Проверка что шаблон существует
    template = session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Деактивировать старое назначение для этого типа
    old_assignments = session.exec(
        select(DocumentTemplateAssignment)
        .where(DocumentTemplateAssignment.document_type == document_type)
    ).all()
    
    for old in old_assignments:
        session.delete(old)
    session.commit()
    
    # Создать новое назначение
    assignment = DocumentTemplateAssignment(
        document_type=document_type,
        template_id=template_id,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    
    logger.info(f"Назначен шаблон {template_id} на тип {document_type}")
    return {
        "id": assignment.id,
        "document_type": document_type,
        "template_id": template_id
    }
