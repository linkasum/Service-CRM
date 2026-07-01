"""
Telegram bot for CRM operators and masters.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Bot, Dispatcher, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from sqlalchemy import func
from sqlmodel import Session, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import get_settings
from core.database import engine
from core.logging import logger
from core.permissions_defs import (
    DEFAULT_ROLE_PERMISSIONS, effective_permissions,
)
from core.security import get_password_hash, verify_password
from models.individual_permission import IndividualPermission
from core.telegram_auth import verify_telegram_link_token
from models.cash_shift import CashShift
from models.cash_transaction import CashTransaction
from models.custom_status import CustomStatus
from models.order import Order
from models.order_comment import OrderComment
from models.order_part import OrderPart
from models.order_service import OrderService
from models.part import Part
from models.role import Role
from models.salary_record import SalaryRecord
from models.service import Service, ServiceStatus
from models.user import User

settings = get_settings()
telegram_proxy_url = (
    os.getenv("TELEGRAM_BOT_PROXY_URL")
    or os.getenv("ALL_PROXY")
    or os.getenv("TELEGRAM_PROXY_URL")
    or os.getenv("HTTPS_PROXY")
    or os.getenv("HTTP_PROXY")
)
bot_session = AiohttpSession(proxy=telegram_proxy_url, timeout=120) if telegram_proxy_url else None
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, session=bot_session)
dp = Dispatcher()

CRM_URL = os.getenv("CRM_FRONTEND_URL", "http://10.20.4.199:5173").rstrip("/")

ROLE_MAP = {1: "admin", 2: "manager", 3: "master", 4: "acceptor", 5: "courier"}
ROLE_LABELS = {
    "admin": "Администратор",
    "manager": "Менеджер",
    "master": "Мастер",
    "acceptor": "Приемщик",
    "courier": "Курьер",
}
def load_statuses():
    with Session(engine) as session:
        statuses = session.exec(
            select(CustomStatus).where(CustomStatus.is_active == True).order_by(CustomStatus.id)
        ).all()
    labels = {s.code: s.name for s in statuses if s.code}
    terminal = {"issued", "issued_br", "cancelled"}
    all_codes = [s.code for s in statuses if s.code]
    active_codes = [c for c in all_codes if c not in terminal]
    buttons = [(s.code, s.name) for s in statuses if s.code and s.code not in ("new",)]
    return labels, active_codes, buttons

STATUS_LABELS, ACTIVE_STATUSES, STATUS_BUTTONS = load_statuses()


class MessageLogMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        text = (event.text or event.caption or "")[:80]
        logger.info(
            f"Telegram message: chat_id={event.chat.id} user_id={user_id} text={text!r}"
        )
        return await handler(event, data)


dp.message.middleware(MessageLogMiddleware())


class OrderState(StatesGroup):
    waiting_comment = State()
    waiting_part_quantity = State()


class ProfileState(StatesGroup):
    waiting_current_password = State()
    waiting_new_password = State()
    waiting_email = State()


def get_role_name(session: Session, user: User) -> str:
    role = session.get(Role, user.role_id) if user.role_id else None
    if role and role.name:
        return role.name
    return ROLE_MAP.get(user.role_id, "user")


def get_user(chat_id: int) -> dict | None:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.telegram_chat_id == chat_id)).first()
        if not user:
            return None
        role = get_role_name(session, user)
        role_perms = set()
        if user.role:
            role_perms = set(user.role.permissions)
        ind_rows = session.exec(
            select(IndividualPermission).where(IndividualPermission.user_id == user.id)
        ).all()
        custom = [ip.permission for ip in ind_rows]
        perms = effective_permissions(role, custom)
        return {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name or user.username,
            "role": role,
            "permissions": perms,
        }


def user_has_perm(user: dict, perm: str) -> bool:
    return perm in user.get("permissions", [])


def require_auth(message: types.Message) -> dict | None:
    user = get_user(message.chat.id)
    return user


def is_admin_role(role: str) -> bool:
    return role in ["admin", "manager", "acceptor"]


def main_keyboard(user: dict) -> ReplyKeyboardMarkup:
    rows: list[list] = []
    perms = set(user.get("permissions", []))

    if "dashboard:view" in perms:
        rows.append([KeyboardButton(text="📊 Дашборд")])
        if "orders:view" in perms:
            if user["role"] == "master":
                rows[-1].append(KeyboardButton(text="📋 Мои заказы"))
            else:
                rows[-1].append(KeyboardButton(text="📋 Заказы"))

    if "orders:view" in perms and "dashboard:view" not in perms:
        if user["role"] == "master":
            rows.append([KeyboardButton(text="📋 Мои заказы")])
        else:
            rows.append([KeyboardButton(text="📋 Заказы")])

    second_row = []
    if "orders:edit" in perms or "orders:status" in perms:
        second_row.append(KeyboardButton(text="💬 Комментарии"))
        if user["role"] == "master":
            second_row.append(KeyboardButton(text="📝 Статус"))

    if "cash:view" in perms or "cash:manage" in perms:
        if user["role"] in ("admin", "manager"):
            second_row.append(KeyboardButton(text="💰 Касса"))
        elif user["role"] != "master":
            second_row.append(KeyboardButton(text="💰 Касса"))

    if second_row:
        rows.append(second_row)

    third_row = []
    if "services:view" in perms:
        third_row.append(KeyboardButton(text="🧰 Услуги"))
    if "parts:view" in perms:
        third_row.append(KeyboardButton(text="📦 Склад"))

    if third_row:
        rows.append(third_row)

    if user["role"] == "master":
        query = query.where(Order.master_id == user["id"])
        rows.append([KeyboardButton(text="💰 Зарплата")])

    fourth_row = []
    if "users:manage" in perms or "settings.manage" in perms:
        fourth_row.append(KeyboardButton(text="⚙️ Управление"))
    if fourth_row:
        rows.append(fourth_row)

    rows.append([KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏠 Меню")])
    rows.append([KeyboardButton(text="🔗 CRM")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def crm_links_keyboard(role: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Открыть CRM", url=CRM_URL)],
        [InlineKeyboardButton(text="Заказы", url=f"{CRM_URL}/orders")],
    ]
    if role in ["admin", "manager", "acceptor"]:
        rows.extend(
            [
                [InlineKeyboardButton(text="Склад", url=f"{CRM_URL}/parts")],
                [InlineKeyboardButton(text="Услуги", url=f"{CRM_URL}/services")],
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_management_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Сотрудники", callback_data="admin:users")],
            [InlineKeyboardButton(text="🔑 Роли", callback_data="admin:roles")],
            [InlineKeyboardButton(text="🔗 Настройки бота", url=f"{CRM_URL}/settings")],
            [InlineKeyboardButton(text="🌐 CRM", url=CRM_URL)],
        ]
    )


def employee_list_keyboard(users: list[User], page: int = 0) -> InlineKeyboardMarkup:
    rows = []
    page_size = 8
    start = page * page_size
    for user in users[start : start + page_size]:
        enabled = "🟢" if user.is_active else "🔴"
        tg = "📱" if user.telegram_chat_id else ""
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{enabled}{tg} {user.full_name or user.username}",
                    callback_data=f"admin:user:{user.id}",
                )
            ]
        )
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="Назад", callback_data=f"admin:users_p:{page - 1}"))
    if start + page_size < len(users):
        nav.append(InlineKeyboardButton(text="Вперед", callback_data=f"admin:users_p:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="Назад к управлению", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def employee_detail_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Смена роли", callback_data=f"admin:changerole:{user_id}")],
            [InlineKeyboardButton(text="Переключить активность", callback_data=f"admin:toggle_active:{user_id}")],
            [InlineKeyboardButton(text="Назад к сотрудникам", callback_data="admin:users")],
        ]
    )


def roles_list_keyboard(roles: list[Role], user_id: int | None = None) -> InlineKeyboardMarkup:
    rows = []
    for role in roles[:10]:
        text = f"{role.name} ({len(role.users)} чел)" if hasattr(role, "users") and role.users else role.name
        if user_id:
            rows.append([InlineKeyboardButton(text=text, callback_data=f"admin:setrole:{user_id}:{role.id}")])
        else:
            rows.append([InlineKeyboardButton(text=text, callback_data=f"admin:role:{role.id}")])
    if user_id:
        rows.append([InlineKeyboardButton(text="Назад к сотруднику", callback_data=f"admin:user:{user_id}")])
    else:
        rows.append([InlineKeyboardButton(text="Назад к управлению", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def rub(value: float | int | None) -> str:
    return f"{float(value or 0):,.0f} ₽".replace(",", " ")


def can_access_order(user: dict, order: Order) -> bool:
    if is_admin_role(user["role"]):
        return True
    if user["role"] == "master":
        return order.master_id == user["id"]
    return False


def orders_query_for_user(user: dict):
    exclude = ["issued", "issued_br", "cancelled"]
    if user["role"] == "master":
        exclude.append("ready_pickup")
    query = select(Order).where(Order.status.not_in(exclude))
    if user["role"] == "master":
        query = query.where(Order.master_id == user["id"])
    return query.order_by(Order.created_at.desc())


def orders_list_keyboard(orders: list[Order], back_callback: str = "menu") -> InlineKeyboardMarkup:
    rows = []
    for order in orders[:15]:
        text = f"#{order.id} {status_label(order.status)} - {order.device_model[:24]}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"order:{order.id}")])
    rows.append([InlineKeyboardButton(text="Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_menu_keyboard(order_id: int, user: dict) -> InlineKeyboardMarkup:
    rows = []
    if user_has_perm(user, "orders:edit"):
        rows.append([InlineKeyboardButton(text="Добавить комментарий", callback_data=f"comment:{order_id}")])
    if user_has_perm(user, "orders:status"):
        rows.append([InlineKeyboardButton(text="Сменить статус", callback_data=f"status:{order_id}")])
    if user_has_perm(user, "parts:writeoff"):
        rows.append([InlineKeyboardButton(text="Списать запчасть", callback_data=f"parts:{order_id}")])
    if user_has_perm(user, "parts:delete_writeoff"):
        rows.append([InlineKeyboardButton(text="Удалить запчасть", callback_data=f"delparts:{order_id}")])
    if user_has_perm(user, "services:add"):
        rows.append([InlineKeyboardButton(text="Добавить услугу", callback_data=f"services:{order_id}")])
    if user_has_perm(user, "services:delete"):
        rows.append([InlineKeyboardButton(text="Удалить услугу", callback_data=f"delservices:{order_id}")])
    rows.append([InlineKeyboardButton(text="Последние комментарии", callback_data=f"comments:{order_id}")])
    rows.append([InlineKeyboardButton(text="Назад к заказам", callback_data="orders")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def status_keyboard(order_id: int, user: dict) -> InlineKeyboardMarkup:
    rows = []
    for status, label in STATUS_BUTTONS:
        if status == "issued" and not user_has_perm(user, "orders:issue"):
            continue
        rows.append([InlineKeyboardButton(text=label, callback_data=f"setstatus:{order_id}:{status}")])
    rows.append([InlineKeyboardButton(text="Назад к заказу", callback_data=f"order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def parts_keyboard(order_id: int, parts: list[Part]) -> InlineKeyboardMarkup:
    rows = []
    for part in parts[:10]:
        text = f"{part.name[:28]} - {part.quantity} шт"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"addpart:{order_id}:{part.id}")])
    rows.append([InlineKeyboardButton(text="Назад к заказу", callback_data=f"order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_parts_keyboard(order_id: int, rows_data: list[tuple[OrderPart, Part]]) -> InlineKeyboardMarkup:
    rows = []
    for order_part, part in rows_data[:10]:
        text = f"{part.name[:26]} x{order_part.quantity}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"delpart:{order_part.id}")])
    rows.append([InlineKeyboardButton(text="Назад к заказу", callback_data=f"order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def services_keyboard(order_id: int, services: list[Service]) -> InlineKeyboardMarkup:
    rows = []
    for service in services[:10]:
        text = f"{service.name[:28]} - {rub(service.price)}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"addservice:{order_id}:{service.id}")])
    rows.append([InlineKeyboardButton(text="Назад к заказу", callback_data=f"order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_services_keyboard(order_id: int, services: list[OrderService]) -> InlineKeyboardMarkup:
    rows = []
    for item in services[:10]:
        text = f"{item.service_name[:28]} x{item.quantity}"
        rows.append([InlineKeyboardButton(text=text, callback_data=f"delservice:{item.id}")])
    rows.append([InlineKeyboardButton(text="Назад к заказу", callback_data=f"order:{order_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kassa_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть смену", callback_data="kassa:open")],
            [InlineKeyboardButton(text="Закрыть смену", callback_data="kassa:close")],
        ]
    )


def format_order(order: Order, comments: list[OrderComment] | None = None) -> str:
    lines = [
        f"Заказ #{order.id}",
        f"Статус: {status_label(order.status)}",
        f"Устройство: {order.device_brand or ''} {order.device_model}".strip(),
        f"Клиент: {order.client_name}",
        f"Телефон: {order.client_phone}",
        f"Проблема: {order.complaint[:300]}",
        f"Сумма: {rub(order.total_cost)}",
    ]
    if order.comment:
        lines.append(f"Примечание: {order.comment[:300]}")
    if comments:
        lines.append("")
        lines.append("Последние комментарии:")
        for comment in comments[:3]:
            created = comment.created_at.strftime("%d.%m %H:%M") if comment.created_at else ""
            lines.append(f"{created} {comment.username}: {comment.text[:180]}")
    return "\n".join(lines)


async def send_orders(message: types.Message, user: dict, title: str) -> None:
    with Session(engine) as session:
        orders = session.exec(orders_query_for_user(user)).all()[:15]
    if not orders:
        await message.answer("Активных заказов нет")
        return
    await message.answer(title, reply_markup=orders_list_keyboard(orders))


async def send_menu(message: types.Message, user: dict) -> None:
    role_label = ROLE_LABELS.get(user["role"], user["role"])
    await message.answer(
        f"{user['full_name']} - {role_label}\nВыберите действие:",
        reply_markup=main_keyboard(user),
    )


async def notify_order_master(order_id: int, text: str, skip_chat_id: int | None = None) -> None:
    try:
        with Session(engine) as session:
            order = session.get(Order, order_id)
            if not order or not order.master_id:
                return
            master = session.get(User, order.master_id)
            if not master or not master.telegram_chat_id:
                return
            if skip_chat_id and master.telegram_chat_id == skip_chat_id:
                return
            await bot.send_message(master.telegram_chat_id, text)
    except Exception as exc:
        logger.warning(f"Telegram notify master failed for order_id={order_id}: {exc}")


@dp.message(Command("ping"))
async def ping_cmd(message: types.Message):
    logger.info(f"Telegram /ping: chat_id={message.chat.id}")
    await message.answer("pong")


@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    args = message.text.split()
    logger.info(f"Telegram /start: chat_id={message.chat.id} args_count={len(args)}")
    if len(args) > 1:
        user_id = verify_telegram_link_token(args[1])
        if not user_id:
            await message.answer(
                "Код привязки неверный или истек. Создайте новый код в CRM: Настройки -> Сотрудники -> TG."
            )
            return

        with Session(engine) as session:
            user = session.get(User, user_id)
            if not user:
                await message.answer("Пользователь не найден")
                return
            if not user.is_active:
                await message.answer("Пользователь неактивен")
                return

            role = get_role_name(session, user)
            if role not in ["admin", "manager", "master", "acceptor", "courier"]:
                await message.answer(f"Роль {role} не разрешена для Telegram")
                return

            linked_user = session.exec(
                select(User).where(
                    User.telegram_chat_id == message.chat.id,
                    User.id != user.id,
                )
            ).first()
            if linked_user:
                await message.answer(
                    f"Этот Telegram уже привязан к сотруднику {linked_user.username}"
                )
                return

            if user.telegram_chat_id and user.telegram_chat_id != message.chat.id:
                await message.answer("Этот сотрудник уже привязан к другому Telegram")
                return

            user.telegram_chat_id = message.chat.id
            session.add(user)
            session.commit()
            logger.info(f"Telegram auth: {user.username}")

        await state.clear()
        current_user = get_user(message.chat.id)
        if current_user:
            await message.answer("Telegram успешно привязан")
            await send_menu(message, current_user)
        return

    user = get_user(message.chat.id)
    if user:
        await state.clear()
        await send_menu(message, user)
        return

    await message.answer(
        "CRM бот\n"
        "Для входа администратор должен создать код в CRM: Настройки -> Сотрудники -> TG.\n"
        "После привязки команда /start будет открывать меню."
    )


@dp.message(Command("menu"))
@dp.message(lambda message: message.text in ["🏠 Меню", "MENU"])
async def menu_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы. Получите код привязки в CRM.")
        return
    await send_menu(message, user)


@dp.message(Command("orders"))
@dp.message(lambda message: message.text in ["📋 Заказы", "📋 Мои заказы", "ZAKAZ", "MOI_ZAKAZ"])
async def orders_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    title = "Мои активные заказы:" if user["role"] == "master" else "Активные заказы:"
    await send_orders(message, user, title)


@dp.message(lambda message: message.text == "📝 Статус")
async def status_shortcut(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    await send_orders(message, user, "Выберите заказ для смены статуса:")


@dp.callback_query(lambda callback: callback.data == "orders")
async def orders_callback(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    with Session(engine) as session:
        orders = session.exec(orders_query_for_user(user)).all()[:15]
    if not orders:
        await callback.message.edit_text("Активных заказов нет")
    else:
        await callback.message.edit_text("Активные заказы:", reply_markup=orders_list_keyboard(orders))
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("order:"))
async def order_selected(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Заказ не найден или нет доступа")
            await callback.answer()
            return
        comments = session.exec(
            select(OrderComment)
            .where(OrderComment.order_id == order_id)
            .order_by(OrderComment.created_at.desc())
            .limit(3)
        ).all()
        await callback.message.answer(
            format_order(order, comments),
            reply_markup=order_menu_keyboard(order_id, user),
        )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("comments:"))
async def order_comments(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        comments = session.exec(
            select(OrderComment)
            .where(OrderComment.order_id == order_id)
            .order_by(OrderComment.created_at.desc())
            .limit(8)
        ).all()
    if not comments:
        await callback.message.answer("Комментариев пока нет")
    else:
        lines = [f"Комментарии к заказу #{order_id}:"]
        for comment in comments:
            created = comment.created_at.strftime("%d.%m %H:%M") if comment.created_at else ""
            lines.append(f"{created} {comment.username}: {comment.text[:250]}")
        await callback.message.answer("\n\n".join(lines))
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("comment:"))
async def add_comment_start(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
    await state.update_data(order_id=order_id)
    await state.set_state(OrderState.waiting_comment)
    await callback.message.answer(f"Напишите комментарий к заказу #{order_id}:")
    await callback.answer()


@dp.message(OrderState.waiting_comment)
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("order_id")
    user = require_auth(message)
    if not user or not order_id:
        await message.answer("Ошибка авторизации")
        await state.clear()
        return
    text = (message.text or message.caption or "").strip()
    if not text:
        await message.answer("Комментарий пустой")
        return
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await message.answer("Заказ не найден или нет доступа")
            await state.clear()
            return
        comment = OrderComment(
            order_id=order_id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=text[:2000],
            is_system=False,
        )
        session.add(comment)
        session.commit()
    await state.clear()
    await message.answer(f"Комментарий добавлен к заказу #{order_id}")
    await notify_order_master(
        order_id,
        f"Новый комментарий к заказу #{order_id} от {user['full_name']}:\n{text[:500]}",
        skip_chat_id=message.chat.id,
    )


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("parts:"))
async def parts_for_order(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        parts = session.exec(
            select(Part).where(Part.quantity > 0).order_by(Part.name).limit(10)
        ).all()
    if not parts:
        await callback.message.answer("На складе нет доступных запчастей")
    else:
        await callback.message.answer(
            f"Выберите запчасть для списания в заказ #{order_id}:",
            reply_markup=parts_keyboard(order_id, parts),
        )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("addpart:"))
async def add_part_start(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    _, order_id_raw, part_id_raw = callback.data.split(":", 2)
    order_id = int(order_id_raw)
    part_id = int(part_id_raw)
    with Session(engine) as session:
        order = session.get(Order, order_id)
        part = session.get(Part, part_id)
        if not order or not can_access_order(user, order) or not part:
            await callback.message.answer("Заказ или запчасть не найдены")
            await callback.answer()
            return
        await state.update_data(order_id=order_id, part_id=part_id)
        await state.set_state(OrderState.waiting_part_quantity)
        await callback.message.answer(
            f"Сколько списать: {part.name}?\nДоступно: {part.quantity} шт"
        )
    await callback.answer()


@dp.message(OrderState.waiting_part_quantity)
async def process_part_quantity(message: types.Message, state: FSMContext):
    user = require_auth(message)
    data = await state.get_data()
    order_id = data.get("order_id")
    part_id = data.get("part_id")
    if not user or not order_id or not part_id:
        await message.answer("Ошибка авторизации")
        await state.clear()
        return
    try:
        quantity = int((message.text or "").strip())
    except ValueError:
        await message.answer("Введите количество числом")
        return
    if quantity <= 0:
        await message.answer("Количество должно быть больше нуля")
        return

    with Session(engine) as session:
        order = session.get(Order, order_id)
        part = session.get(Part, part_id)
        if not order or not can_access_order(user, order) or not part:
            await message.answer("Заказ или запчасть не найдены")
            await state.clear()
            return
        if part.quantity < quantity:
            await message.answer(f"Недостаточно на складе. Доступно: {part.quantity} шт")
            return

        added_cost = part.sale_price * quantity
        part.quantity -= quantity
        order_part = OrderPart(
            order_id=order.id,
            part_id=part.id,
            quantity=quantity,
            price_at_order=part.sale_price,
            master_id=user["id"],
        )
        order.parts_cost = (order.parts_cost or 0) + added_cost
        order.total_cost = (order.total_cost or 0) + added_cost
        comment = OrderComment(
            order_id=order.id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=f"Списана запчасть: {part.name} x{quantity} = {rub(added_cost)}",
            is_system=True,
        )
        part_name = part.name
        session.add(part)
        session.add(order)
        session.add(order_part)
        session.add(comment)
        session.commit()

    await state.clear()
    await message.answer(f"Запчасть списана в заказ #{order_id}: {part_name} x{quantity}")
    await notify_order_master(
        order_id,
        f"По заказу #{order_id} списана запчасть: {part_name} x{quantity}",
        skip_chat_id=message.chat.id,
    )


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delparts:"))
async def delete_parts_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        rows = session.exec(
            select(OrderPart, Part)
            .join(Part, OrderPart.part_id == Part.id)
            .where(OrderPart.order_id == order_id)
            .order_by(OrderPart.created_at.desc())
        ).all()
    if not rows:
        await callback.message.answer("В заказе нет списанных запчастей")
    else:
        await callback.message.answer(
            "Выберите списание для удаления:",
            reply_markup=order_parts_keyboard(order_id, rows),
        )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delpart:"))
async def delete_order_part(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_part_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order_part = session.get(OrderPart, order_part_id)
        if not order_part:
            await callback.message.answer("Списание не найдено")
            await callback.answer()
            return
        order = session.get(Order, order_part.order_id)
        part = session.get(Part, order_part.part_id)
        if not order or not part or not can_access_order(user, order):
            await callback.message.answer("Нет доступа")
            await callback.answer()
            return
        removed_cost = order_part.price_at_order * order_part.quantity
        part.quantity += order_part.quantity
        order.parts_cost = max((order.parts_cost or 0) - removed_cost, 0)
        order.total_cost = max((order.total_cost or 0) - removed_cost, 0)
        comment = OrderComment(
            order_id=order.id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=f"Удалено списание запчасти: {part.name} x{order_part.quantity}",
            is_system=True,
        )
        order_id = order.id
        part_name = part.name
        quantity = order_part.quantity
        session.delete(order_part)
        session.add(part)
        session.add(order)
        session.add(comment)
        session.commit()
    await callback.message.answer(f"Списание удалено: {part_name} x{quantity}")
    await notify_order_master(
        order_id,
        f"По заказу #{order_id} удалено списание запчасти: {part_name} x{quantity}",
        skip_chat_id=callback.from_user.id,
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("services:"))
async def services_for_order(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        services = session.exec(
            select(Service)
            .where(Service.status == ServiceStatus.active)
            .order_by(Service.name)
            .limit(10)
        ).all()
    if not services:
        await callback.message.answer("Активных услуг нет")
    else:
        await callback.message.answer(
            f"Выберите услугу для заказа #{order_id}:",
            reply_markup=services_keyboard(order_id, services),
        )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("addservice:"))
async def add_service_to_order(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    _, order_id_raw, service_id_raw = callback.data.split(":", 2)
    order_id = int(order_id_raw)
    service_id = int(service_id_raw)
    with Session(engine) as session:
        order = session.get(Order, order_id)
        service = session.get(Service, service_id)
        if not order or not can_access_order(user, order) or not service:
            await callback.message.answer("Заказ или услуга не найдены")
            await callback.answer()
            return
        item = OrderService(
            order_id=order.id,
            service_id=service.id,
            service_name=service.name,
            price_at_order=service.price,
            quantity=1,
        )
        order.work_cost = (order.work_cost or 0) + service.price
        order.total_cost = (order.total_cost or 0) + service.price
        comment = OrderComment(
            order_id=order.id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=f"Добавлена услуга: {service.name} = {rub(service.price)}",
            is_system=True,
        )
        service_name = service.name
        service_price = service.price
        session.add(order)
        session.add(item)
        session.add(comment)
        session.commit()
    await callback.message.answer(f"Услуга добавлена: {service_name} ({rub(service_price)})")
    await notify_order_master(
        order_id,
        f"По заказу #{order_id} добавлена услуга: {service_name} ({rub(service_price)})",
        skip_chat_id=callback.from_user.id,
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delservices:"))
async def delete_services_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        services = session.exec(
            select(OrderService)
            .where(OrderService.order_id == order_id)
            .order_by(OrderService.created_at.desc())
        ).all()
    if not services:
        await callback.message.answer("В заказе нет услуг")
    else:
        await callback.message.answer(
            "Выберите услугу для удаления:",
            reply_markup=order_services_keyboard(order_id, services),
        )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("delservice:"))
async def delete_order_service(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    item_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        item = session.get(OrderService, item_id)
        if not item:
            await callback.message.answer("Услуга не найдена")
            await callback.answer()
            return
        order = session.get(Order, item.order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа")
            await callback.answer()
            return
        removed_cost = item.price_at_order * item.quantity
        order.work_cost = max((order.work_cost or 0) - removed_cost, 0)
        order.total_cost = max((order.total_cost or 0) - removed_cost, 0)
        comment = OrderComment(
            order_id=order.id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=f"Удалена услуга: {item.service_name} x{item.quantity}",
            is_system=True,
        )
        order_id = order.id
        service_name = item.service_name
        session.delete(item)
        session.add(order)
        session.add(comment)
        session.commit()
    await callback.message.answer(f"Услуга удалена: {service_name}")
    await notify_order_master(
        order_id,
        f"По заказу #{order_id} удалена услуга: {service_name}",
        skip_chat_id=callback.from_user.id,
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("status:"))
async def status_menu(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    order_id = int(callback.data.split(":", 1)[1])
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
    await callback.message.answer(
        f"Выберите новый статус для заказа #{order_id}:",
        reply_markup=status_keyboard(order_id, user),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("setstatus:"))
async def change_status(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    _, order_id_raw, new_status = callback.data.split(":", 2)
    order_id = int(order_id_raw)
    with Session(engine) as session:
        order = session.get(Order, order_id)
        if not order or not can_access_order(user, order):
            await callback.message.answer("Нет доступа к заказу")
            await callback.answer()
            return
        old_status = order.status
        if old_status in ("issued", "issued_br") and new_status not in ("issued", "issued_br"):
            await callback.message.answer("Заказ уже выдан. Смена статуса невозможна.")
            await callback.answer()
            return
        order.status = new_status
        if new_status == "ready":
            order.ready_at = datetime.utcnow()
        if new_status == "issued":
            order.issued_at = datetime.utcnow()
            if order.master_id and order.total_cost:
                try:
                    from routes.salary_assignment import auto_assign_salary
                    master_user = session.get(User, order.master_id)
                    salary_res = auto_assign_salary(
                        order_id=order.id, session=session, current_user=master_user,
                    )
                    if not salary_res.get("already_accrued"):
                        logger.info(f"Bot: Зарплата за заказ #{order.id}: {salary_res.get('salary_amount', 0)}₽")
                except Exception as exc:
                    logger.warning(f"Bot: Ошибка начисления ЗП по заказу #{order.id}: {exc}")
        comment = OrderComment(
            order_id=order_id,
            user_id=user["id"],
            username=user["username"],
            role_name=user["role"],
            text=f"Статус изменен: {status_label(old_status)} -> {status_label(new_status)}",
            is_system=True,
        )
        session.add(order)
        session.add(comment)
        session.commit()
        await callback.message.answer(
            f"Заказ #{order_id}: {status_label(old_status)} -> {status_label(new_status)}"
        )
    try:
        client_user = session.exec(
            select(User).where(User.phone == order.client_phone)
        ).first()
        if client_user and client_user.telegram_chat_id:
            device = f"{order.device_brand or ''} {order.device_model}".strip()
            if new_status == "ready_pickup":
                text = f"Ваш заказ #{order_id} готов к выдаче\nУстройство: {device}\nСтоимость: {rub(order.total_cost)}"
            else:
                text = f"Статус заказа #{order_id}: {status_label(new_status)}\nУстройство: {device}"
            await bot.send_message(client_user.telegram_chat_id, text)
    except Exception as exc:
        logger.warning(f"Bot: Ошибка уведомления клиента по заказу #{order_id}: {exc}")
    await notify_order_master(
        order_id,
        f"Статус заказа #{order_id} изменен: {status_label(old_status)} -> {status_label(new_status)}",
        skip_chat_id=callback.message.chat.id,
    )
    await callback.answer()


@dp.message(lambda message: message.text == "💬 Комментарии")
async def comments_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    with Session(engine) as session:
        query = select(OrderComment, Order).join(Order, OrderComment.order_id == Order.id)
        if user["role"] == "master":
            query = query.where(Order.master_id == user["id"])
        query = query.order_by(OrderComment.created_at.desc()).limit(10)
        rows = session.exec(query).all()
    if not rows:
        await message.answer("Комментариев пока нет")
        return
    lines = ["Последние комментарии:"]
    for comment, order in rows:
        created = comment.created_at.strftime("%d.%m %H:%M") if comment.created_at else ""
        lines.append(f"#{order.id} {created} {comment.username}: {comment.text[:180]}")
    await message.answer("\n\n".join(lines))


@dp.message(lambda message: message.text in ["💰 Зарплата", "SALARY"])
async def salary_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    now = datetime.utcnow()
    period_start = datetime(now.year, now.month, 1) if now.day <= 15 else datetime(now.year, now.month, 16)
    if now.day <= 15:
        period_end = datetime(now.year, now.month, 15, 23, 59, 59)
    elif now.month < 12:
        period_end = datetime(now.year, now.month + 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
    with Session(engine) as session:
        records = session.exec(
            select(SalaryRecord).where(
                SalaryRecord.user_id == user["id"],
                SalaryRecord.period_start >= period_start,
                SalaryRecord.period_start <= period_end,
            )
        ).all()
    accrued = sum(record.calculated_amount for record in records if record.status == "accrued")
    deducted = sum(abs(record.calculated_amount) for record in records if record.status == "deducted")
    paid = sum(abs(record.calculated_amount) for record in records if record.status == "paid")
    net = accrued - deducted
    balance = net - paid
    await message.answer(
        f"Зарплата {period_start.strftime('%d.%m')}-{period_end.strftime('%d.%m')}:\n"
        f"Начислено: {rub(accrued)}\n"
        f"Удержано: {rub(deducted)}\n"
        f"Выплачено: {rub(paid)}\n"
        f"Остаток: {rub(max(balance, 0))}\n"
        f"Записей: {len(records)}"
    )


@dp.message(lambda message: message.text in ["🧰 Услуги", "USLUGI"])
async def services_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    with Session(engine) as session:
        services = session.exec(
            select(Service)
            .where(Service.status == ServiceStatus.active)
            .order_by(Service.name)
            .limit(20)
        ).all()
    if not services:
        await message.answer("Активных услуг нет")
        return
    lines = ["Активные услуги:"]
    for service in services:
        duration = f", {service.duration_minutes} мин" if service.duration_minutes else ""
        lines.append(f"#{service.id} {service.name}: {rub(service.price)}{duration}")
    await message.answer("\n".join(lines))


@dp.message(lambda message: message.text in ["📦 Склад", "SKLAD"])
async def parts_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    with Session(engine) as session:
        parts = session.exec(select(Part).order_by(Part.quantity, Part.name).limit(20)).all()
    if not parts:
        await message.answer("Склад пуст")
        return
    lines = ["Склад: первые 20 позиций по остатку:"]
    for part in parts:
        lines.append(
            f"#{part.id} {part.name} ({part.article}) - {part.quantity} шт, {rub(part.sale_price)}"
        )
    await message.answer("\n".join(lines))


@dp.message(lambda message: message.text in ["📊 Дашборд", "DASH", "STAT"])
async def dashboard_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    with Session(engine) as session:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        def count(extra_where=None):
            q = select(func.count(Order.id))
            if user["role"] == "master":
                q = q.where(Order.master_id == user["id"])
            if extra_where is not None:
                q = q.where(extra_where)
            return session.exec(q).one()
        today_count = count(Order.created_at >= today)
        active_count = count(Order.status.not_in(["issued", "issued_br", "cancelled", "ready_pickup"]))
        repair_count = count(Order.status == "repair")
        ready_count = count(Order.status == "ready")
    await message.answer(
        "Дашборд:\n"
        f"Заказов сегодня: {today_count}\n"
        f"Активных: {active_count}\n"
        f"В ремонте: {repair_count}\n"
        f"Готово: {ready_count}"
    )


@dp.message(lambda message: message.text == "💰 Касса")
async def kassa_cmd(message: types.Message):
    user = require_auth(message)
    if not user or user["role"] not in ["admin", "manager"]:
        await message.answer("Нет доступа")
        return
    with Session(engine) as session:
        last = session.exec(
            select(CashShift)
            .where(CashShift.is_open == False)
            .order_by(CashShift.closed_at.desc())
        ).first()
        shift = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
    if shift:
        await message.answer(
            f"Касса: смена #{shift.id} открыта\nБаланс: {rub(shift.initial_amount)}",
            reply_markup=kassa_keyboard(),
        )
    else:
        last_amount = last.final_amount if last else 0
        await message.answer(
            f"Касса закрыта\nПоследний остаток: {rub(last_amount)}",
            reply_markup=kassa_keyboard(),
        )


@dp.callback_query(lambda callback: callback.data == "kassa:open")
async def kassa_open(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or user["role"] not in ["admin", "manager"] or not callback.message:
        await callback.answer()
        return
    with Session(engine) as session:
        open_shift = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
        if open_shift:
            await callback.message.answer(f"Смена #{open_shift.id} уже открыта")
            await callback.answer()
            return
        last = session.exec(
            select(CashShift)
            .where(CashShift.is_open == False)
            .order_by(CashShift.closed_at.desc())
        ).first()
        amount = last.final_amount if last else 0
        shift = CashShift(opened_by=user["id"], initial_amount=amount, is_open=True)
        session.add(shift)
        session.commit()
    await callback.message.answer(f"Смена открыта\nНачальная сумма: {rub(amount)}")
    await callback.answer()


@dp.callback_query(lambda callback: callback.data == "kassa:close")
async def kassa_close(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or user["role"] not in ["admin", "manager"] or not callback.message:
        await callback.answer()
        return
    from models.cash_transaction import CashTransaction

    with Session(engine) as session:
        shift = session.exec(select(CashShift).where(CashShift.is_open == True)).first()
        if not shift:
            await callback.message.answer("Открытой смены нет")
            await callback.answer()
            return
        transactions = session.exec(
            select(CashTransaction).where(CashTransaction.shift_id == shift.id)
        ).all()
        initial_amount = shift.initial_amount
        income = sum(tx.amount for tx in transactions if tx.amount > 0)
        expense = sum(abs(tx.amount) for tx in transactions if tx.amount < 0)
        final = initial_amount + income - expense
        shift.final_amount = final
        shift.is_open = False
        shift.closed_by = user["id"]
        shift.closed_at = datetime.utcnow()
        session.add(shift)
        session.commit()
    await callback.message.answer(
        f"Смена закрыта\nНачало: {rub(initial_amount)}\nПриход: {rub(income)}\nРасход: {rub(expense)}\nИтого: {rub(final)}"
    )
    await callback.answer()


@dp.message(lambda message: message.text == "⚙️ Управление")
async def admin_management_cmd(message: types.Message):
    user = require_auth(message)
    if not user or user["role"] != "admin":
        await message.answer("Нет доступа")
        return
    await message.answer(
        "Управление системой:",
        reply_markup=admin_management_keyboard(),
    )


@dp.message(lambda message: message.text == "🔗 CRM")
async def crm_links_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    await message.answer(
        "Web-интерфейс CRM:",
        reply_markup=crm_links_keyboard(user["role"]),
    )


@dp.callback_query(lambda callback: callback.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    await callback.message.answer(
        "Управление системой:",
        reply_markup=admin_management_keyboard(),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data == "admin:users")
async def admin_users_list(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    with Session(engine) as session:
        users = session.exec(select(User).order_by(User.is_active.desc(), User.username)).all()
    await callback.message.answer(
        f"Сотрудники ({len(users)}):",
        reply_markup=employee_list_keyboard(list(users)),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("admin:users_p:"))
async def admin_users_page(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    page = int(callback.data.split(":")[2])
    with Session(engine) as session:
        users = session.exec(select(User).order_by(User.is_active.desc(), User.username)).all()
    await callback.message.edit_text(
        f"Сотрудники ({len(users)}):",
        reply_markup=employee_list_keyboard(list(users), page),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("admin:user:"))
async def admin_user_detail(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    user_id = int(callback.data.split(":")[2])
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            await callback.message.answer("Сотрудник не найден")
            await callback.answer()
            return
        role = session.get(Role, user.role_id) if user.role_id else None
    lines = [
        f"Сотрудник: {user.full_name or user.username}",
        f"Логин: {user.username}",
        f"Роль: {role.name if role else '—'}",
        f"Telegram: {'привязан' if user.telegram_chat_id else '—'}",
        f"Активен: {'да' if user.is_active else 'нет'}",
    ]
    if user.email:
        lines.append(f"Email: {user.email}")
    if user.phone:
        lines.append(f"Телефон: {user.phone}")
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=employee_detail_keyboard(user.id),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("admin:changerole:"))
async def admin_change_role_menu(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    user_id = int(callback.data.split(":")[2])
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            await callback.message.answer("Сотрудник не найден")
            await callback.answer()
            return
        roles = session.exec(select(Role).order_by(Role.id)).all()
    await callback.message.answer(
        f"Выберите роль для {user.full_name or user.username}:",
        reply_markup=roles_list_keyboard(list(roles), user_id),
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("admin:setrole:"))
async def admin_set_role(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    _, user_id_raw, role_id_raw = callback.data.split(":", 4)
    user_id = int(user_id_raw)
    role_id = int(role_id_raw)
    with Session(engine) as session:
        user = session.get(User, user_id)
        role = session.get(Role, role_id)
        if not user or not role:
            await callback.message.answer("Ошибка")
            await callback.answer()
            return
        old_role = session.get(Role, user.role_id) if user.role_id else None
        user.role_id = role.id
        session.add(user)
        session.commit()
    await callback.message.answer(
        f"Роль {user.full_name or user.username}: "
        f"{old_role.name if old_role else '—'} → {role.name}"
    )
    await callback.answer()


@dp.callback_query(lambda callback: callback.data and callback.data.startswith("admin:toggle_active:"))
async def admin_toggle_active(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    user_id = int(callback.data.split(":")[2])
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            await callback.message.answer("Сотрудник не найден")
            await callback.answer()
            return
        if user.id == 1 and user.username == "admin":
            await callback.message.answer("Нельзя деактивировать главного администратора")
            await callback.answer()
            return
        user.is_active = not user.is_active
        session.add(user)
        session.commit()
        status = "активен" if user.is_active else "деактивирован"
    await callback.message.answer(f"{user.full_name or user.username} теперь {status}")
    await callback.answer()


@dp.callback_query(lambda callback: callback.data == "admin:roles")
async def admin_roles_list(callback: CallbackQuery):
    if not callback.message:
        await callback.answer()
        return
    with Session(engine) as session:
        roles = session.exec(select(Role).order_by(Role.id)).all()
        results = []
        for role in roles:
            count = session.exec(
                select(func.count(User.id)).where(User.role_id == role.id)
            ).one()
            results.append((role, count))
    if not results:
        await callback.message.answer("Роли не найдены")
        await callback.answer()
        return
    lines = ["Роли:"]
    for role, count in results:
        lines.append(f"#{role.id} {role.name} — {count} чел")
    lines.append("")
    lines.append("Управление ролями доступно в web CRM")
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Управление в CRM", url=f"{CRM_URL}/settings")],
                [InlineKeyboardButton(text="Назад к управлению", callback_data="admin:menu")],
            ]
        ),
    )
    await callback.answer()


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔒 Сменить пароль", callback_data="profile:password")],
            [InlineKeyboardButton(text="📧 Изменить email", callback_data="profile:email")],
        ]
    )


@dp.message(lambda message: message.text == "👤 Профиль")
async def profile_cmd(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    with Session(engine) as session:
        db_user = session.get(User, user["id"])
        if not db_user:
            await message.answer("Пользователь не найден")
            return
        role = get_role_name(session, db_user)
    lines = [
        f"Профиль: {db_user.full_name or db_user.username}",
        f"Логин: {db_user.username}",
        f"Роль: {role}",
        f"Email: {db_user.email or 'не указан'}",
        f"Телефон: {db_user.phone or 'не указан'}",
        f"Telegram: {'привязан' if db_user.telegram_chat_id else 'не привязан'}",
    ]
    await message.answer("\n".join(lines), reply_markup=profile_keyboard())


@dp.callback_query(lambda callback: callback.data == "profile:password")
async def profile_change_password_start(callback: CallbackQuery, state: FSMContext):
    if not callback.message:
        await callback.answer()
        return
    await state.set_state(ProfileState.waiting_current_password)
    await callback.message.answer("Введите текущий пароль:")
    await callback.answer()


@dp.message(ProfileState.waiting_current_password)
async def profile_check_current_password(message: types.Message, state: FSMContext):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        await state.clear()
        return
    current = (message.text or "").strip()
    with Session(engine) as session:
        db_user = session.get(User, user["id"])
        if not db_user or not verify_password(current, db_user.password_hash):
            await message.answer("Неверный пароль")
            await state.clear()
            return
    await state.update_data(user_id=user["id"])
    await state.set_state(ProfileState.waiting_new_password)
    await message.answer("Введите новый пароль:")


@dp.message(ProfileState.waiting_new_password)
async def profile_set_new_password(message: types.Message, state: FSMContext):
    new_password = (message.text or "").strip()
    if len(new_password) < 4:
        await message.answer("Пароль должен быть не менее 4 символов")
        return
    data = await state.get_data()
    user_id = data.get("user_id")
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return
        db_user.password_hash = get_password_hash(new_password)
        session.add(db_user)
        session.commit()
    await state.clear()
    await message.answer("Пароль успешно изменен")


@dp.callback_query(lambda callback: callback.data == "profile:email")
async def profile_change_email_start(callback: CallbackQuery, state: FSMContext):
    if not callback.message:
        await callback.answer()
        return
    user = get_user(callback.from_user.id)
    if not user:
        await callback.message.answer("Вы не авторизованы")
        await callback.answer()
        return
    await state.update_data(user_id=user["id"])
    await state.set_state(ProfileState.waiting_email)
    await callback.message.answer("Введите новый email:")
    await callback.answer()


@dp.message(ProfileState.waiting_email)
async def profile_set_email(message: types.Message, state: FSMContext):
    email = (message.text or "").strip()
    if not email or "@" not in email:
        await message.answer("Введите корректный email")
        return
    data = await state.get_data()
    user_id = data.get("user_id")
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return
        db_user.email = email
        session.add(db_user)
        session.commit()
    await state.clear()
    await message.answer(f"Email изменен на {email}")

@dp.message(lambda message: message.text in ["KLIENT", "DOK", "OTCHET", "NASTROIKI"])
async def legacy_cmds(message: types.Message):
    user = require_auth(message)
    if not user:
        await message.answer("Вы не авторизованы")
        return
    await message.answer("Эта команда перенесена в русское меню. Нажмите 🏠 Меню.")


@dp.message()
async def fallback_msg(message: types.Message):
    user = require_auth(message)
    if user:
        await message.answer("Команда не распознана. Нажмите 🏠 Меню.")
        return
    await message.answer("Вы не авторизованы. Получите код привязки в CRM.")


async def start_bot():
    logger.info("Bot started")
    await dp.start_polling(bot)


async def stop_bot():
    await bot.session.close()
    logger.info("Bot stopped")

@dp.callback_query(lambda callback: callback.data == "menu")
async def menu_callback(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    if not user or not callback.message:
        await callback.answer()
        return
    role_label = ROLE_LABELS.get(user["role"], user["role"])
    await callback.message.edit_text(
        f"{user[full_name]} - {role_label}\nВыберите действие:",
        reply_markup=main_keyboard(user),
    )
    await callback.answer()

