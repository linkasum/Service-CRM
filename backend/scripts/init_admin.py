"""
Скрипт создания начального супер-администратора при первом запуске
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select
from core.database import engine, create_db_and_tables
from core.security import get_password_hash
from models.role import Role
from models.user import User
from models.company_settings import CompanySettings
from models.document_template import DocumentTemplate
from models.custom_status import CustomStatus
from models.brand import Brand
from models.category import Category
from models.client_source import ClientSource
from models.age_group import AgeGroup
from core.logging import logger


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"


def init_admin():
    """Создать таблицы и роль администратора с пользователем"""
    create_db_and_tables()
    logger.info("Таблицы созданы")
    """Создать роль администратора и пользователя, если их нет"""
    with Session(engine) as session:
        # Проверка существования роли admin
        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                permissions=[
                    "order.create", "order.view", "order.edit", "order.delete",
                    "client.view", "client.edit",
                    "part.create", "part.view", "part.edit", "part.delete",
                    "salary.view", "salary.edit", "salary.manage",
                    "report.view",
                    "role.manage",
                    "user.manage",
                    "settings.manage",
                    "template.manage",
                ],
                description="Администратор — полные права доступа"
            )
            session.add(admin_role)
            session.commit()
            session.refresh(admin_role)
            logger.info("Создана роль: admin")
        else:
            logger.info("Роль admin уже существует")

        # Проверка существования пользователя admin
        admin_user = session.exec(select(User).where(User.username == DEFAULT_ADMIN_USERNAME)).first()
        if not admin_user:
            admin_user = User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role_id=admin_role.id,
                is_active=True,
            )
            session.add(admin_user)
            session.commit()
            logger.info(f"Создан пользователь: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}")
        else:
            logger.info("Пользователь admin уже существует")

        # Создание других ролей, если их нет
        default_roles = [
            {
                "name": "manager",
                "permissions": ["order.create", "order.view", "order.edit", "client.view", "client.edit", "part.view", "report.view"],
                "description": "Менеджер — приём заказов, управление клиентами"
            },
            {
                "name": "master",
                "permissions": ["order.view", "order.edit"],
                "description": "Мастер — просмотр и выполнение заказов"
            },
            {
                "name": "acceptor",
                "permissions": ["order.create", "order.view", "order.edit", "client.view", "client.edit"],
                "description": "Приёмщик — приём техники, оформление заказов"
            },
            {
                "name": "courier",
                "permissions": ["order.view"],
                "description": "Курьер — просмотр заказов"
            },
        ]

        for role_data in default_roles:
            existing = session.exec(select(Role).where(Role.name == role_data["name"])).first()
            if not existing:
                role = Role(**role_data)
                session.add(role)
                logger.info(f"Создана роль: {role_data['name']}")

        session.commit()

        # Создание настроек компании по умолчанию
        company_settings = session.exec(select(CompanySettings)).first()
        if not company_settings:
            company_settings = CompanySettings()
            session.add(company_settings)
            session.commit()
            logger.info("Созданы настройки компании по умолчанию")

        # Создание шаблонов документов по умолчанию
        default_templates = [
            {
                "type": "receipt",
                "content_template": "КВИТАНЦИЯ ПРИЁМА\n\nКлиент: {client_name}\nТелефон: {client_phone}\nУстройство: {device_model}\nНеисправность: {complaint}\n\nДата приёма: {created_at}\nСумма: {total_cost} руб.",
            },
            {
                "type": "diagnostic_act",
                "content_template": "АКТ ДИАГНОСТИКИ\n\nЗаказ #{order_id}\nУстройство: {device_model}\n\nВыявленные дефекты:\n{diagnostic_act_text}\n\nРекомендуемая стоимость ремонта: {total_cost} руб.",
            },
            {
                "type": "work_act",
                "content_template": "АКТ ВЫПОЛНЕННЫХ РАБОТ\n\nЗаказ #{order_id}\nКлиент: {client_name}\nУстройство: {device_model}\n\nВыполненные работы:\n{complaint}\n\nИтого: {total_cost} руб.\nГарантия: {warranty_days} дней\n\nДата выдачи: {issued_at}",
            },
            {
                "type": "invoice",
                "content_template": "СЧЁТ\n\n{company_name}\nИНН: {company_inn}\nАдрес: {company_address}\nТел: {company_phone}\n\nЗаказ #{order_id}\nКлиент: {client_name}\nУстройство: {device_model}\n\nСумма: {total_cost} руб.",
            },
        ]

        for tmpl_data in default_templates:
            existing = session.exec(select(DocumentTemplate).where(DocumentTemplate.type == tmpl_data["type"])).first()
            if not existing:
                tmpl = DocumentTemplate(**tmpl_data)
                session.add(tmpl)
                logger.info(f"Создан шаблон: {tmpl_data['type']}")

        session.commit()
        logger.info("Инициализация завершена")

    # Стандартные статусы
    default_statuses = [
        {"name": "Новый", "color": "#1890ff", "is_default": True},
        {"name": "Диагностика", "color": "#faad14"},
        {"name": "Согласование", "color": "#fa8c16"},
        {"name": "В работе", "color": "#722ed1"},
        {"name": "Ожидает запчасти", "color": "#13c2c2"},
        {"name": "Готов", "color": "#52c41a"},
        {"name": "На выдаче", "color": "#eb2f96"},
        {"name": "Выдан", "color": "#d9d9d9"},
        {"name": "Выдан БР", "color": "#d9d9d9"},
        {"name": "Отменён", "color": "#f5222d"},
    ]
    for sd in default_statuses:
        existing = session.exec(select(CustomStatus).where(CustomStatus.name == sd["name"])).first()
        if not existing:
            session.add(CustomStatus(**sd))
    logger.info("Созданы стандартные статусы")

    # Стандартные бренды
    default_brands = ["Apple", "Samsung", "Xiaomi", "Huawei", "Honor", "Sony", "LG", "HP", "Dell", "Asus", "Acer", "Lenovo"]
    for bname in default_brands:
        existing = session.exec(select(Brand).where(Brand.name == bname)).first()
        if not existing:
            session.add(Brand(name=bname))
    logger.info("Созданы стандартные бренды")

    # Стандартные категории
    default_categories = ["Смартфон", "Ноутбук", "Планшет", "Телевизор", "Компьютер", "Бытовая техника"]
    for cname in default_categories:
        existing = session.exec(select(Category).where(Category.name == cname)).first()
        if not existing:
            session.add(Category(name=cname))
    logger.info("Созданы стандартные категории")

    # Стандартные источники клиентов
    default_sources = ["Прямой визит", "Рекомендация", "Google", "Яндекс", "Соцсети", "Баннер", "Пенсионер", "Avito", "2ГИС", "Сайт"]
    for sname in default_sources:
        existing = session.exec(select(ClientSource).where(ClientSource.name == sname)).first()
        if not existing:
            session.add(ClientSource(name=sname))
    logger.info("Созданы стандартные источники клиентов")

    # Стандартные возрастные группы
    default_age_groups = ["0-20", "Студент", "Взрослый", "Пенсионер"]
    for agname in default_age_groups:
        existing = session.exec(select(AgeGroup).where(AgeGroup.name == agname)).first()
        if not existing:
            session.add(AgeGroup(name=agname))
    logger.info("Созданы стандартные возрастные группы")

    session.commit()


if __name__ == "__main__":
    init_admin()
