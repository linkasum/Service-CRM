"""
Permissions: role matrix, individual overrides, current user check.
Uses Role.permissions (JSON) + IndividualPermission (table) for overrides.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from core.database import get_session
from core.security import get_current_user, require_permission
from core.permissions_defs import (
    ALL_PERMISSION_STRINGS, DEFAULT_ROLE_PERMISSIONS,
    SECTION_PERMISSIONS, SECTION_LABELS, ACTION_LABELS,
)
from models.user import User
from models.role import Role
from models.individual_permission import IndividualPermission
from core.logging import logger

router = APIRouter(prefix="/api/permissions", tags=["Разрешения"])


def effective_permissions(session: Session, user: User) -> list[str]:
    role = session.get(Role, user.role_id) if user.role_id else None
    perms = set(role.permissions) if role else set()
    ind_rows = session.exec(
        select(IndividualPermission).where(IndividualPermission.user_id == user.id)
    ).all()
    for ip in ind_rows:
        if ip.permission.startswith("-"):
            perms.discard(ip.permission[1:])
        else:
            perms.add(ip.permission)
    return sorted(perms)


@router.get("/my", summary="Мой набор прав")
def my_permissions(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    perms = effective_permissions(session, current_user)
    matrix = {}
    for section, actions in SECTION_PERMISSIONS.items():
        granted = [a for a in actions if a in perms]
        if granted:
            matrix[section] = granted
    return {"permissions": perms, "sections": matrix}


@router.get("/roles-summary", summary="Сводка прав по всем ролям")
def roles_summary(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    roles = session.exec(select(Role).order_by(Role.id)).all()
    result = []
    for role in roles:
        perms = set(role.permissions)
        matrix = {}
        for section, actions in SECTION_PERMISSIONS.items():
            matrix[section] = {a: a in perms for a in actions}
        result.append({"role_name": role.name, "role_id": role.id, "matrix": matrix})
    return {
        "roles": result,
        "sections": {
            s: {"label": SECTION_LABELS[s],
                "actions": {a: ACTION_LABELS.get(a, a) for a in acts}}
            for s, acts in SECTION_PERMISSIONS.items()
        },
    }


@router.put("/roles-batch", summary="Сохранить права для нескольких ролей")
def batch_save_role_perms(
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    """data = {"roles": {"admin": ["orders:view", ...], "master": [...], ...}}"""
    allowed = set(ALL_PERMISSION_STRINGS)
    updated = {}
    for role_name, perms in data.get("roles", {}).items():
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            continue
        clean = sorted(p for p in set(perms) if p in allowed)
        role.permissions = clean
        session.add(role)
        updated[role_name] = len(clean)
    session.commit()
    logger.info(f"Batch permissions saved: {updated}")
    return {"updated": updated}


@router.post("/seed", summary="Заполнить права по умолчанию")
def seed_defaults(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("role.manage")),
):
    seeded = {}
    for role_name, perms in DEFAULT_ROLE_PERMISSIONS.items():
        role = session.exec(select(Role).where(Role.name == role_name)).first()
        if not role:
            continue
        if role.permissions:
            continue
        role.permissions = sorted(perms)
        session.add(role)
        seeded[role_name] = len(perms)
    session.commit()
    if seeded:
        logger.info(f"Seeded default permissions: {seeded}")
    return {"seeded": seeded}


# === Индивидуальные разрешения ===

@router.get("/individual", summary="Индивидуальные разрешения")
def get_individual(session: Session = Depends(get_session)):
    rows = session.exec(select(IndividualPermission).order_by(IndividualPermission.user_id)).all()
    result = []
    for ip in rows:
        user = session.get(User, ip.user_id)
        role = session.get(Role, user.role_id) if user and user.role_id else None
        result.append({
            "id": ip.id, "user_id": ip.user_id, "permission": ip.permission,
            "username": user.username if user else None,
            "role_name": role.name if role else None,
        })
    return result


@router.post("/individual", summary="Добавить индивидуальное разрешение")
def add_individual(data: dict, session: Session = Depends(get_session),
                   current_user: User = Depends(require_permission("role.manage"))):
    ip = IndividualPermission(user_id=data["user_id"], permission=data["permission"])
    session.add(ip); session.commit(); session.refresh(ip)
    return ip


@router.delete("/individual/{ip_id}", summary="Удалить индивидуальное")
def remove_individual(ip_id: int, session: Session = Depends(get_session),
                      current_user: User = Depends(require_permission("role.manage"))):
    ip = session.get(IndividualPermission, ip_id)
    if not ip: raise HTTPException(404, "Не найдено")
    session.delete(ip); session.commit()
    return {"message": "Удалено"}
