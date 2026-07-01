"""
Симулятор рабочего процесса сервисного центра
Полный цикл: приемка → диагностика → согласование → ремонт → готов → выдан
Использование:
    cd backend
    source venv/bin/activate
    python scripts/simulate_work_week.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from core.database import get_session, engine
from models.user import User
from models.role import Role
from models.order import Order
from models.client import Client
from models.brand import Brand
from models.category import Category
from models.device_model import DeviceModel
from models.cash_shift import CashShift
from models.cash_transaction import CashTransaction, TransactionType
from models.order_payment import OrderPayment
from models.order_service import OrderService
from models.order_part import OrderPart
from models.part import Part
from models.salary_record import SalaryRecord
from models.salary_config import SalaryConfig
from models.work_schedule import WorkSchedule
from models.order_comment import OrderComment
from models.custom_status import CustomStatus
from sqlalchemy import text

# Данные для симуляции
CLIENT_NAMES = [
    ("Иванов", "Иван", "+79057200140", "Иванов Иван Иванович"),
    ("Петров", "Петр", "+79161234567", "Петров Петр Петрович"),
    ("Сидоров", "Сидор", "+79267654321", "Сидоров Сидор Сидорович"),
    ("Смирнова", "Анна", "+79031112233", "Смирнова Анна Ивановна"),
    ("Кузнецов", "Дмитрий", "+79169998877", "Кузнецов Дмитрий Александрович"),
    ("Попова", "Елена", "+79265554433", "Попова Елена Сергеевна"),
    ("Васильев", "Андрей", "+79032223344", "Васильев Андрей Николаевич"),
    ("Морозова", "Ольга", "+79168887766", "Морозова Ольга Владимировна"),
    ("Новиков", "Сергей", "+79261110099", "Новиков Сергей Михайлович"),
    ("Федорова", "Наталья", "+79034445566", "Федорова Наталья Игоревна"),
]

DEVICE_DATA = [
    ("phone", "Apple", "iPhone 14 Pro", "Не включается"),
    ("phone", "Samsung", "Galaxy S23", "Разбит экран"),
    ("laptop", "Apple", "MacBook Pro 16", "Не заряжается"),
    ("laptop", "Lenovo", "ThinkPad X1", "Проблемы с клавиатурой"),
    ("tablet", "Apple", "iPad Air", "Не работает сенсор"),
    ("robot_vacuum", "Xiaomi", "Mi Robot Vacuum", "Не выезжает щетка"),
    ("vacuum", "Dyson", "V15 Detect", "Не держит заряд"),
    ("coffee_machine", "DeLonghi", "Magnifica S", "Не греет воду"),
    ("tv", "LG", "OLED55C1", "Нет изображения"),
    ("microwave", "Samsung", "MS23K3513", "Не крутится тарелка"),
]

SERVICES_LIST = [
    ("Диагностика", 0, True),  # Бесплатно при ремонте
    ("Замена дисплея", 1500, False),
    ("Замена аккумулятора", 800, False),
    ("Программный ремонт", 1200, False),
    ("Чистка от жидкости", 2000, False),
    ("Замена разъёма", 1000, False),
    ("Комплексная диагностика", 500, False),
    ("Настройка ПО", 600, False),
]

PARTS_LIST = [
    ("Дисплей iPhone 14 Pro", 15000, 8000),
    ("Аккумулятор iPhone 14 Pro", 4500, 2000),
    ("Дисплей Samsung S23", 12000, 6000),
    ("Аккумулятор Samsung S23", 3500, 1500),
    ("Клавиатура MacBook", 8000, 4000),
    ("Разъём зарядки iPad", 2000, 800),
    ("Щетка для Dyson", 1500, 600),
    ("Аккумулятор Dyson", 6000, 2500),
]

# Статусы заказа
STATUS_FLOW = [
    "new",  # Новый
    "diagnostics",  # Диагностика
    "agreed",  # Согласован
    "repair",  # В ремонте
    "waiting_parts",  # Ждёт запчасти
    "ready",  # Готов
    "ready_pickup",  # Готов к выдаче
    "issued",  # Выдан
]


def get_or_create_user(session: Session, username: str, role_name: str, telegram_chat_id: int = None):
    """Получить или создать пользователя"""
    role = session.exec(select(Role).where(Role.name == role_name)).first()
    if not role:
        role = Role(name=role_name, permissions=[], description=f"Роль {role_name}")
        session.add(role)
        session.commit()
        session.refresh(role)
    
    user = session.exec(select(User).where(User.username == username)).first()
    if not user:
        user = User(
            username=username,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS3MebAJu",  # admin
            role_id=role.id,
            telegram_chat_id=telegram_chat_id,
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def get_or_create_client(session: Session, name: str, phone: str, client_type: str = "individual"):
    """Получить или создать клиента"""
    client = session.exec(select(Client).where(Client.phone == phone)).first()
    if not client:
        client = Client(
            name=name,
            phone=phone,
            client_type=client_type,
            email=f"{name.lower()}@example.com",
        )
        session.add(client)
        session.commit()
        session.refresh(client)
    return client


def create_salary_config_if_not_exists(session: Session):
    """Создать конфигурацию зарплаты если не существует"""
    config = session.exec(select(SalaryConfig).where(SalaryConfig.is_active == True)).first()
    if not config:
        config = SalaryConfig(
            formula_string="total * 0.3",  # 30% от стоимости работ
            is_active=True,
            description="Стандартная формула: 30% от стоимости работ",
        )
        session.add(config)
        session.commit()
    return config


def open_cash_shift(session: Session, user: User, date: datetime, start_balance: int = 0):
    """Открыть кассовую смену"""
    # Проверяем есть ли открытая смена
    open_shift = session.exec(
        select(CashShift).where(
            CashShift.opened_by == user.id,
            CashShift.is_open == True
        )
    ).first()
    
    if open_shift:
        print(f"  💰 Смена уже открыта (ID={open_shift.id})")
        return open_shift
    
    shift = CashShift(
        opened_by=user.id,
        opened_at=date,
        initial_amount=start_balance,
        is_open=True,
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    print(f"  💰 Открыта смена ID={shift.id} (баланс: {start_balance}₽)")
    return shift


def close_cash_shift(session: Session, shift: CashShift, user: User, date: datetime):
    """Закрыть кассовую смену"""
    # Считаем итоговую сумму
    total_income = session.exec(
        select(func.sum(CashTransaction.amount)).where(
            CashTransaction.shift_id == shift.id,
            CashTransaction.transaction_type == TransactionType.income
        )
    ).first() or 0
    
    total_expense = session.exec(
        select(func.sum(CashTransaction.amount)).where(
            CashTransaction.shift_id == shift.id,
            CashTransaction.transaction_type == TransactionType.expense
        )
    ).first() or 0
    
    shift.closed_at = date
    shift.final_amount = shift.initial_amount + total_income - total_expense
    shift.is_open = False
    session.add(shift)
    session.commit()
    print(f"  💰 Закрыта смена ID={shift.id} (доход: {total_income}₽, расход: {total_expense}₽, итог: {shift.final_amount}₽)")
    return shift


def create_work_schedule(session: Session, user: User, date: datetime, is_working: bool = True):
    """Создать запись в графике работы"""
    existing = session.exec(
        select(WorkSchedule).where(
            WorkSchedule.user_id == user.id,
            WorkSchedule.date == date.date()
        )
    ).first()
    
    if not existing:
        # Если не работает - не создаём запись
        if not is_working:
            print(f"  📅 {user.username}: выходной ({date.date()})")
            return
        
        schedule = WorkSchedule(
            user_id=user.id,
            date=date.date(),
        )
        session.add(schedule)
        session.commit()
        print(f"  📅 {user.username}: работает ({date.date()})")
    else:
        print(f"  📅 {user.username}: уже запланирован ({date.date()})")


def create_order(session: Session, acceptor: User, master: User, client: Client, device_data: tuple, date: datetime):
    """Создать заказ"""
    category, brand_name, model, problem = device_data
    
    # Получаем бренд
    brand = session.exec(select(Brand).where(Brand.name == brand_name)).first()
    if not brand:
        brand = Brand(name=brand_name, is_active=True)
        session.add(brand)
        session.commit()
        session.refresh(brand)
    
    order = Order(
        client_name=client.name,
        client_phone=client.phone,
        client_type=client.client_type,
        client_email=client.email,
        device_category=category,
        device_brand=brand_name,
        device_model=model,
        problem_description=problem,
        status="new",
        acceptor_id=acceptor.id,
        manager_name=acceptor.username,
        master_id=master.id,
        created_at=date,
        updated_at=date,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    
    # Создаём комментарий о приёмке
    comment = OrderComment(
        order_id=order.id,
        user_id=acceptor.id,
        username=acceptor.username,
        role_name=acceptor.role.name if acceptor.role else "",
        text=f"📋 Заказ принят. Устройство: {brand_name} {model}. Проблема: {problem}",
        is_system=True,
        created_at=date,
    )
    session.add(comment)
    session.commit()
    
    print(f"  📦 Заказ #{order.id}: {client.name} - {brand_name} {model} ({problem})")
    return order


def update_order_status(session: Session, order: Order, new_status: str, user: User, date: datetime):
    """Обновить статус заказа"""
    old_status = order.status
    order.status = new_status
    # updated_at нет в модели, пропускаем
    session.add(order)
    
    # Комментарий
    status_names = {
        "new": "Новый",
        "diagnostics": "Диагностика",
        "agreed": "Согласован",
        "repair": "В ремонте",
        "waiting_parts": "Ждёт запчасти",
        "ready": "Готов",
        "ready_pickup": "Готов к выдаче",
        "issued": "Выдан",
    }
    
    comment = OrderComment(
        order_id=order.id,
        user_id=user.id,
        username=user.username,
        role_name=user.role.name if user.role else "",
        text=f"🔄 Статус изменён: {status_names.get(old_status, old_status)} → {status_names.get(new_status, new_status)}",
        is_system=True,
        created_at=date,
    )
    session.add(comment)
    session.commit()
    print(f"    🔄 Статус: {status_names.get(old_status, old_status)} → {status_names.get(new_status, new_status)}")


def add_service_to_order(session: Session, order: Order, service_name: str, cost: int, user: User, date: datetime):
    """Добавить услугу к заказу"""
    service = OrderService(
        order_id=order.id,
        service_name=service_name,
        cost=cost,
        performed_by=order.master_id,
        created_at=date,
    )
    session.add(service)
    session.commit()
    print(f"    🔧 Услуга: {service_name} ({cost}₽)")
    return service


def add_part_to_order(session: Session, order: Order, part_name: str, cost_price: int, sale_price: int, user: User, date: datetime):
    """Добавить запчасть к заказу"""
    # Проверяем есть ли запчасть в базе
    part = session.exec(select(Part).where(Part.name == part_name)).first()
    if not part:
        part = Part(
            name=part_name,
            article=f"ART-{random.randint(10000, 99999)}",
            quantity=10,
            cost_price=cost_price,
            sale_price=sale_price,
        )
        session.add(part)
        session.commit()
        session.refresh(part)
    
    order_part = OrderPart(
        order_id=order.id,
        part_id=part.id,
        quantity=1,
        price_at_order=sale_price,
        cost_price_at_order=cost_price,
    )
    session.add(order_part)
    
    # Уменьшаем количество на складе
    part.quantity -= 1
    session.add(part)
    session.commit()
    
    print(f"    ⚙️ Запчасть: {part_name} ({sale_price}₽)")
    return order_part


def make_payment(session: Session, order: Order, amount: int, shift: CashShift, user: User, date: datetime):
    """Внести оплату по заказу"""
    payment = OrderPayment(
        order_id=order.id,
        amount=amount,
        payment_method="cash",
        status="completed",
        comment="Оплата наличными",
    )
    session.add(payment)
    
    # Кассовая операция
    transaction = CashTransaction(
        shift_id=shift.id,
        amount=amount,
        transaction_type=TransactionType.income,
        description=f"Оплата по заказу #{order.id}",
        order_id=order.id,
        created_by=user.id,
        created_at=date,
    )
    session.add(transaction)
    session.commit()
    
    print(f"    💵 Оплата: {amount}₽")
    return payment


def calculate_salary(session: Session, order: Order, master: User, date: datetime):
    """Рассчитать зарплату мастеру"""
    config = session.exec(select(SalaryConfig).where(SalaryConfig.is_active == True)).first()
    if not config:
        return None
    
    # Считаем стоимость работ
    services = session.exec(select(OrderService).where(OrderService.order_id == order.id)).all()
    total_work = sum(s.price_at_order * s.quantity for s in services)
    
    parts = session.exec(select(OrderPart).where(OrderPart.order_id == order.id)).all()
    parts_cost = sum(p.price_at_order * p.quantity for p in parts)
    
    total_cost = total_work + parts_cost
    
    # По формуле
    import simpleeval
    s = simpleeval.SimpleEval()
    s.names = {
        "total_cost": total_cost,
        "parts_cost": parts_cost,
        "work": total_work,
        "total": total_work,
        "parts": parts_cost,
        "warranty": 0
    }
    salary_amount = int(s.eval(config.formula_string))
    
    record = SalaryRecord(
        user_id=master.id,
        order_id=order.id,
        calculated_amount=salary_amount,
        status="accrued",
        period_start=date.replace(day=1),  # Начало месяца
        period_end=date.replace(day=15) if date.day < 15 else date.replace(day=date.day),  # Конец периода
        comment=f"Зарплата по заказу #{order.id}",
        created_at=date,
    )
    session.add(record)
    session.commit()
    
    print(f"    💰 Зарплата мастеру: {salary_amount}₽")
    return record


def simulate_day(session: Session, date: datetime, day_num: int, acceptors: list, masters: list):
    """Симуляция одного рабочего дня"""
    print(f"\n{'='*70}")
    print(f"📅 ДЕНЬ {day_num}: {date.strftime('%d.%m.%Y')} ({date.strftime('%A')})")
    print(f"{'='*70}")
    
    # Выбираем случайного приёмщика из работающих сегодня
    working_acceptors = []
    for acceptor in acceptors:
        schedule = session.exec(
            select(WorkSchedule).where(
                WorkSchedule.user_id == acceptor.id,
                WorkSchedule.date == date.date()
            )
        ).first()
        if schedule:  # Если запись есть - работает
            working_acceptors.append(acceptor)
    
    if not working_acceptors:
        print(f"  😴 Сегодня выходной у всех приёмщиков")
        return
    
    acceptor = random.choice(working_acceptors)
    master = random.choice(masters) if masters else acceptor
    
    # Открытие смены в 10:00
    shift = open_cash_shift(session, acceptor, date.replace(hour=10, minute=0), start_balance=0)
    
    # Приём заказов (3-5 заказов в день)
    num_orders = random.randint(3, 5)
    print(f"\n📦 ПРИЁМ ЗАКАЗОВ ({num_orders} шт):")
    
    orders = []
    for i in range(num_orders):
        client_data = random.choice(CLIENT_NAMES)
        client = get_or_create_client(
            session,
            f"{client_data[0]} {client_data[1]}",
            client_data[2],
        )
        
        device_data = random.choice(DEVICE_DATA)
        order = create_order(session, acceptor, master, client, device_data, date.replace(hour=10, minute=random.randint(5, 59)))
        orders.append({"order": order, "status_idx": 0})
    
    # Через 2 часа - диагностика
    print(f"\n🔍 ДИАГНОСТИКА:")
    for order_data in orders:
        order = order_data["order"]
        update_order_status(session, order, "diagnostics", acceptor, date.replace(hour=12, minute=random.randint(0, 59)))
        order_data["status_idx"] = 1
    
    # Ещё через час - согласование с клиентом
    print(f"\n✅ СОГЛАСОВАНИЕ С КЛИЕНТОМ:")
    for order_data in orders:
        order = order_data["order"]
        update_order_status(session, order, "agreed", acceptor, date.replace(hour=13, minute=random.randint(0, 59)))
        
        # Добавляем услуги
        num_services = random.randint(1, 3)
        selected_services = random.sample(SERVICES_LIST[1:], num_services)  # Без диагностики
        for service in selected_services:
            add_service_to_order(session, order, service[0], service[1], acceptor, date)
        
        # 50% заказов требуют запчасти
        if random.random() < 0.5:
            part = random.choice(PARTS_LIST)
            add_part_to_order(session, order, part[0], part[1], part[2], acceptor, date)
            update_order_status(session, order, "waiting_parts", acceptor, date.replace(hour=14, minute=random.randint(0, 59)))
            order_data["needs_parts"] = True
        else:
            update_order_status(session, order, "repair", acceptor, date.replace(hour=14, minute=random.randint(0, 59)))
        
        order_data["status_idx"] = 2
    
    # Через 3 часа - ремонт завершён (для тех у кого не было запчастей)
    print(f"\n🔧 ЗАВЕРШЕНИЕ РЕМОНТА:")
    for order_data in orders:
        order = order_data["order"]
        if not order_data.get("needs_parts"):
            update_order_status(session, order, "ready", master, date.replace(hour=17, minute=random.randint(0, 59)))
            order_data["status_idx"] = 5
    
    # На следующий день - запчасти получены, ремонт завершён
    next_day = date + timedelta(days=1)
    print(f"\n📦 ПОЛУЧЕНИЕ ЗАПЧАСТЕЙ (на следующий день):")
    for order_data in orders:
        order = order_data["order"]
        if order_data.get("needs_parts"):
            update_order_status(session, order, "repair", acceptor, next_day.replace(hour=11, minute=random.randint(0, 59)))
            update_order_status(session, order, "ready", master, next_day.replace(hour=16, minute=random.randint(0, 59)))
            order_data["status_idx"] = 5
    
    # Оплата (50% заказов оплачивают сразу, 50% при получении)
    print(f"\n💵 ОПЛАТА:")
    for order_data in orders:
        order = order_data["order"]
        services = session.exec(select(OrderService).where(OrderService.order_id == order.id)).all()
        parts = session.exec(select(OrderPart).where(OrderPart.order_id == order.id)).all()
        total = sum(s.price_at_order * s.quantity for s in services) + sum(p.price_at_order * p.quantity for p in parts)
        
        # Если заказ готов к выдаче - оплачивают
        if order_data["status_idx"] >= 5:
            make_payment(session, order, total, shift, acceptor, date.replace(hour=18, minute=random.randint(0, 59)))
            order_data["paid"] = True
    
    # Выдача заказов (те что оплачены)
    print(f"\n📤 ВЫДАЧА ЗАКАЗОВ:")
    for order_data in orders:
        order = order_data["order"]
        if order_data.get("paid"):
            update_order_status(session, order, "ready_pickup", acceptor, date.replace(hour=19, minute=random.randint(0, 59)))
            update_order_status(session, order, "issued", acceptor, date.replace(hour=19, minute=random.randint(30, 59)))
            
            # Начисляем зарплату
            calculate_salary(session, order, master, date)
            order_data["status_idx"] = 7
    
    # Закрытие смены в 20:00
    close_cash_shift(session, shift, acceptor, date.replace(hour=20, minute=0))
    
    print(f"\n✅ День завершён!")


def main():
    print("="*70)
    print("🏪 СИМУЛЯТОР РАБОЧЕГО ПРОЦЕССА СЕРВИСНОГО ЦЕНТРА")
    print("="*70)
    
    session = next(get_session())
    
    # Очищаем старые данные
    print("\n🧹 ОЧИСТКА СТАРЫХ ДАННЫХ...")
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM salary_records"))
        conn.execute(text("DELETE FROM order_payments"))
        conn.execute(text("DELETE FROM order_parts"))
        conn.execute(text("DELETE FROM order_services"))
        conn.execute(text("DELETE FROM order_comments"))
        conn.execute(text("DELETE FROM cash_transactions"))
        conn.execute(text("DELETE FROM cash_shifts"))
        conn.execute(text("DELETE FROM work_schedules"))
        conn.execute(text("DELETE FROM orders"))
        conn.commit()
    print("✅ Старые данные удалены")
    
    # Получаем пользователей
    print("\n👥 ПОЛЬЗОВАТЕЛИ:")
    
    # Получаем приёмщиков (фиксированная ЗП)
    acceptors = session.exec(
        select(User).join(Role).where(Role.name == "acceptor")
    ).all()
    
    # Получаем мастеров (сдельная ЗП)
    masters = session.exec(
        select(User).join(Role).where(Role.name == "master")
    ).all()
    
    if not acceptors or len(acceptors) == 0:
        print("  ⚠️  Приёмщики не найдены, создаём Елену...")
        elena = get_or_create_user(session, "Елена", "acceptor", telegram_chat_id=123456789)
        acceptors = [elena]
    else:
        elena = acceptors[0]  # Используем первого приёмщика
    
    if not masters or len(masters) == 0:
        print("  ⚠️  Мастера не найдены, используем админа...")
        admin = session.exec(select(User).where(User.username == "admin")).first()
        masters = [admin] if admin else []
    
    print(f"  ✅ Приёмщики ({len(acceptors)}): {', '.join([a.username for a in acceptors])}")
    print(f"  ✅ Мастера ({len(masters)}): {', '.join([m.username for m in masters])}")
    
    # Создаём конфигурацию зарплаты
    create_salary_config_if_not_exists(session)
    
    # Создаём график работы на неделю (3 через 3 для приёмщиков по очереди)
    print("\n📅 ГРАФИК РАБОТЫ (3 через 3 для приёмщиков по очереди):")
    start_date = datetime.now() - timedelta(days=7)  # Начинаем с неделю назад
    
    for i in range(14):  # 2 недели
        date = start_date + timedelta(days=i)
        
        # Приёмщики работают по очереди 3 через 3
        # Первый приёмщик работает дни 0-2, 6-8, 12-14...
        # Второй приёмщик работает дни 3-5, 9-11, 15-17...
        cycle_day = i % 6  # 6-дневный цикл
        working_acceptor_idx = 0 if cycle_day < 3 else 1
        
        for idx, acceptor in enumerate(acceptors[:2]):  # Берём только первых двух приёмщиков
            is_working = (idx == working_acceptor_idx)
            create_work_schedule(session, acceptor, date, is_working)
        
        # Мастера работают каждый день (не добавляем в график, они сдельщики)
    
    # Симуляция каждого дня
    print("\n🚀 НАЧАЛО СИМУЛЯЦИИ...")
    for i in range(7):  # 7 дней
        date = start_date + timedelta(days=i)
        simulate_day(session, date, i + 1, acceptors, masters)
    
    print("\n" + "="*70)
    print("✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА!")
    print("="*70)
    
    # Итоговая статистика
    total_orders = session.exec(select(func.count(Order.id))).first()
    total_revenue = session.exec(
        select(func.sum(OrderPayment.amount)).where(OrderPayment.status == "completed")
    ).first() or 0
    total_salary = session.exec(select(func.sum(SalaryRecord.calculated_amount))).first() or 0
    
    print(f"\n📊 ИТОГИ НЕДЕЛИ:")
    print(f"  📦 Всего заказов: {total_orders}")
    print(f"  💵 Выручка: {total_revenue}₽")
    print(f"  💰 Начислено зарплаты: {total_salary}₽")
    print(f"  👥 Мастеров: 3 (Алексей, Дмитрий, Сергей)")
    print(f"  📅 Приёмщик: Елена (график 3 через 3)")
    print("="*70)


if __name__ == "__main__":
    main()
