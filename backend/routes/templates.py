"""
Маршруты управления шаблонами документов
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.document_template import DocumentTemplate
from core.logging import logger

router = APIRouter(prefix="/api/templates", tags=["Шаблоны документов"])


@router.get("/", summary="Список шаблонов")
def get_templates(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    templates = session.exec(select(DocumentTemplate)).all()
    return [
        {
            "id": t.id,
            "type": t.type,
            "content_template": t.content_template,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in templates
    ]


@router.get("/{template_id}", summary="Шаблон по ID")
def get_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    template = session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    return {
        "id": template.id,
        "type": template.type,
        "content_template": template.content_template,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }


@router.post("/", summary="Создать шаблон")
def create_template(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Проверка существующего
    existing = session.exec(
        select(DocumentTemplate).where(DocumentTemplate.type == data["type"])
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Шаблон для типа '{data['type']}' уже существует")

    template = DocumentTemplate(
        type=data["type"],
        content_template=data.get("content_template", ""),
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    logger.info(f"Создан шаблон: {template.type}")
    return {
        "id": template.id,
        "type": template.type,
        "content_template": template.content_template,
    }


@router.patch("/{template_id}", summary="Обновить шаблон")
def update_template(
    template_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    template = session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")

    if "content_template" in data:
        template.content_template = data["content_template"]

    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    return {
        "id": template.id,
        "type": template.type,
        "content_template": template.content_template,
        "updated_at": template.updated_at.isoformat(),
    }


@router.delete("/{template_id}", summary="Удалить шаблон")
def delete_template(
    template_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    template = session.get(DocumentTemplate, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    session.delete(template)
    session.commit()
    return {"message": f"Шаблон '{template.type}' удалён"}


@router.delete("/by-type/{template_type}", summary="Удалить шаблон по типу")
def delete_template_by_type(
    template_type: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    template = session.exec(
        select(DocumentTemplate).where(DocumentTemplate.type == template_type)
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    session.delete(template)
    session.commit()
    return {"message": f"Шаблон '{template.type}' удалён"}
