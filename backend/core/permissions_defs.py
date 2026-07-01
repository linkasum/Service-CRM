"""
Permission system for CRM.
Each section has view/edit/manage level.
Default role-permission matrix with human-readable labels.
"""

SECTION_PERMISSIONS: dict[str, list[str]] = {
    "orders": ["orders:view", "orders:create", "orders:edit",
               "orders:status", "orders:issue", "orders:delete"],
    "parts": ["parts:view", "parts:writeoff", "parts:delete_writeoff"],
    "services": ["services:view", "services:add", "services:delete"],
    "cash": ["cash:view", "cash:manage"],
    "users": ["users:view", "users:manage"],
    "dashboard": ["dashboard:view"],
    "settings": ["settings.manage"],
    "roles": ["role.manage"],
}

SECTION_LABELS: dict[str, str] = {
    "orders": "Заказы", "parts": "Склад", "services": "Услуги",
    "cash": "Касса", "users": "Сотрудники", "dashboard": "Дашборд",
    "settings": "Настройки", "roles": "Роли",
}

ACTION_LABELS: dict[str, str] = {
    "orders:view": "Просмотр", "orders:create": "Создание",
    "orders:edit": "Редактирование", "orders:status": "Смена статуса",
    "orders:issue": "Статус 'Выдан'", "orders:delete": "Удаление заказа",
    "parts:view": "Просмотр", "parts:writeoff": "Списание в заказ",
    "parts:delete_writeoff": "Удаление из заказа",
    "services:view": "Просмотр", "services:add": "Добавление в заказ",
    "services:delete": "Удаление из заказа",
    "cash:view": "Просмотр", "cash:manage": "Операции",
    "users:view": "Просмотр", "users:manage": "Управление",
    "dashboard:view": "Доступ",
    "settings.manage": "Управление",
    "role.manage": "Управление",
}

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [
        "orders:view", "orders:create", "orders:edit",
        "orders:status", "orders:issue", "orders:delete",
        "parts:view", "parts:writeoff", "parts:delete_writeoff",
        "services:view", "services:add", "services:delete",
        "cash:view", "cash:manage", "cash:access",
        "users:view", "users:manage",
        "dashboard:view",
        "settings.manage",
        "role.manage",
    ],
    "manager": [
        "orders:view", "orders:create", "orders:edit", "orders:status", "orders:issue",
        "parts:view", "parts:writeoff", "parts:delete_writeoff",
        "services:view", "services:add", "services:delete",
        "cash:view", "cash:manage", "cash:access",
        "users:view",
        "dashboard:view",
    ],
    "acceptor": [
        "orders:view", "orders:create", "orders:edit", "orders:status", "orders:issue",
        "parts:view", "parts:writeoff", "parts:delete_writeoff",
        "services:view", "services:add", "services:delete",
        "users:view",
        "dashboard:view",
    ],
    "master": [
        "orders:view", "orders:edit", "orders:status",
        "parts:view", "parts:writeoff",
        "services:view", "services:add",
        "dashboard:view",
    ],
    "courier": [
        "orders:view",
        "dashboard:view",
    ],
}

ALL_PERMISSION_STRINGS = sorted(
    {perm for perms in SECTION_PERMISSIONS.values() for perm in perms}
)


def effective_permissions(role_name: str, custom_perms: list[str] | None = None) -> list[str]:
    defaults = set(DEFAULT_ROLE_PERMISSIONS.get(role_name, []))
    for p in (custom_perms or []):
        if p.startswith("-"):
            defaults.discard(p[1:])
        else:
            defaults.add(p)
    return sorted(defaults)
