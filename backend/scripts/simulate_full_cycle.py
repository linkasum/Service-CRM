"""
Полный симулятор рабочего процесса - ИСПРАВЛЕННЫЙ
Запуск: cd backend && source venv/bin/activate && python scripts/simulate_full_cycle.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, func
from core.database import get_session
from models.user import User
from models.role import Role
from models.order import Order
from models.client import Client
from models.order_service import OrderService
from models.order_part import OrderPart
from models.cash_shift import CashShift
from models.cash_transaction import CashTransaction, TransactionType
from models.order_payment import OrderPayment
from models.salary_record import SalaryRecord
from models.salary_config import SalaryConfig
from models.work_schedule import WorkSchedule
from models.order_comment import OrderComment
from sqlalchemy import text


# Данные
CLIENTS = [
    ("Иванов", "Иван", "+79051111111"),
    ("Петров", "Петр", "+79052222222"),
    ("Сидоров", "Сидор", "+79053333333"),
    ("Смирнова", "Анна", "+79054444444"),
    ("Кузнецов", "Дмитрий", "+79055555555"),
    ("Попова", "Елена", "+79056666666"),
    ("Васильев", "Андрей", "+79057777777"),
    ("Морозова", "Ольга", "+79058888888"),
    ("Новиков", "Сергей", "+79059999999"),
    ("Федорова", "Наталья", "+79050000000"),
]

DEVICES = [
    ("Apple", "iPhone 14 Pro", "Не включается"),
    ("Samsung", "Galaxy S23", "Разбит экран"),
    ("Apple", "MacBook Pro", "Не заряжается"),
    ("Lenovo", "ThinkPad X1", "Проблемы с клавиатурой"),
    ("LG", "OLED55C1", "Нет изображения"),
    ("Samsung", "MS23K3513", "Не греет"),
    ("Dyson", "V15 Detect", "Не держит заряд"),
    ("DeLonghi", "Magnifica S", "Не греет воду"),
    ("Xiaomi", "Mi Robot Vacuum", "Не едет"),
    ("Apple", "iPad Air", "Не работает сенсор"),
]

SERVICES = [
    ("Диагностика", 500),
    ("Замена дисплея", 1500),
    ("Замена аккумулятора", 800),
    ("Программный ремонт", 1200),
    ("Чистка", 1000),
]


def main():
    print("="*70)
    print("🏪 ПОЛНЫЙ СИМУЛЯТОР РАБОЧЕГО ПРОЦЕССА")
    print("="*70)
    
    session = next(get_session())
    
    # 1. Очищаем всё
    print("\n🧹 ОЧИСТКА ДАННЫХ...")
    with session.begin():
        session.execute(text("DELETE FROM salary_records"))
        session.execute(text("DELETE FROM order_payments"))
        session.execute(text("DELETE FROM order_parts"))
        session.execute(text("DELETE FROM order_services"))
        session.execute(text("DELETE FROM order_comments"))
        session.execute(text("DELETE FROM cash_transactions"))
        session.execute(text("DELETE FROM cash_shifts"))
        session.execute(text("DELETE FROM work_schedules"))
        session.execute(text("DELETE FROM orders"))
    print("✅ Удалено всё")
    
    # 2. Получаем пользователей
    print("\n👥 ПОЛЬЗОВАТЕЛИ:")
    acceptors = session.exec(select(User).join(Role).where(Role.name == "acceptor")).all()
    masters = session.exec(select(User).join(Role).where(Role.name == "master")).all()
    
    if not acceptors:
        print("❌ Нет приёмщиков! Создайте роль 'acceptor' и пользователя")
        return
    
    if not masters:
        print("❌ Нет мастеров! Создайте роль 'master' и пользователей")
        return
    
    print(f"  Приёмщики: {', '.join([a.username for a in acceptors])}")
    print(f"  Мастера: {', '.join([m.username for m in masters])}")
    
    # 3. Создаём заказы (10 штук) от лица Елены
    print("\n📦 ПРИЁМ 10 ЗАКАЗОВ (Елена)...")
    
    elena = acceptors[0]
    orders = []
    
    for i in range(10):
        client_data = random.choice(CLIENTS)
        device = random.choice(DEVICES)
        master = random.choice(masters)
        
        # Создаём клиента если нет
        client = session.exec(select(Client).where(Client.phone == client_data[2])).first()
        if not client:
            client = Client(
                name=f"{client_data[0]} {client_data[1]}",
                phone=client_data[2],
                client_type="individual",
            )
            session.add(client)
            session.commit()
            session.refresh(client)
        
        # Создаём заказ
        order = Order(
            client_name=client.name,
            client_phone=client.phone,
            client_type=client.client_type,
            device_category="phone",
            device_brand=device[0],
            device_model=device[1],
            problem_description=device[2],
            status="new",
            acceptor_id=elena.id,
            manager_name=elena.username,
            master_id=master.id,
        )
        session.add(order)
        session.commit()
        session.refresh(order)
        
        orders.append({
            "order": order,
            "master": master,
            "client": client,
            "device": device,
        })
        
        print(f"  ✅ Заказ #{order.id}: {client.name} - {device[0]} {device[1]} (Мастер: {master.username})")
    
    # 4. Проходим полный цикл для каждого заказа
    print("\n🔄 ПОЛНЫЙ ЦИКЛ ДЛЯ ВСЕХ ЗАКАЗОВ...")
    
    # Открываем смену
    shift = CashShift(
        opened_by=elena.id,
        opened_at=datetime.now(),
        initial_amount=0,
        is_open=True,
    )
    session.add(shift)
    session.commit()
    session.refresh(shift)
    print(f"\n💰 Открыта смена #{shift.id}")
    
    total_revenue = 0
    total_salary = 0
    
    for order_data in orders:
        order = order_data["order"]
        master = order_data["master"]
        device = order_data["device"]
        
        print(f"\n  📋 Заказ #{order.id}:")
        
        # 1. Диагностика
        order.status = "diagnostics"
        session.add(order)
        session.commit()
        print(f"    🔍 Диагностика")
        
        # 2. Согласование
        order.status = "agreed"
        session.add(order)
        session.commit()
        print(f"    ✅ Согласован")
        
        # 3. Добавляем услуги (2-3 случайные)
        selected_services = random.sample(SERVICES, random.randint(2, 3))
        service_total = 0
        for svc_name, svc_price in selected_services:
            service = OrderService(
                order_id=order.id,
                service_name=svc_name,
                price_at_order=svc_price,
                quantity=1,
            )
            session.add(service)
            service_total += svc_price
            print(f"    🔧 {svc_name}: {svc_price}₽")
        
        # 4. 50% заказов требуют запчасти
        parts_total = 0
        if random.random() < 0.5:
            parts_cost = random.randint(500, 3000)
            parts_price = parts_cost * 1.5  # Наценка 50%
            parts_total = parts_price
            
            part = OrderPart(
                order_id=order.id,
                part_id=1,  # Фиктивный ID
                quantity=1,
                price_at_order=parts_price,
                cost_price_at_order=parts_cost,
            )
            session.add(part)
            print(f"    ⚙️ Запчасть: {parts_price}₽")
            
            # Статус: ждёт запчасти
            order.status = "waiting_parts"
            session.add(order)
            session.commit()
            print(f"    ⏳ Ждёт запчасти")
        
        # 5. Ремонт
        order.status = "repair"
        session.add(order)
        session.commit()
        print(f"    🔧 В ремонте")
        
        # 6. Готов
        order.status = "ready"
        session.add(order)
        session.commit()
        print(f"    ✅ Готов")
        
        # 7. Готов к выдаче
        order.status = "ready_pickup"
        session.add(order)
        session.commit()
        print(f"    📦 Готов к выдаче")
        
        # 8. Оплата
        total_amount = service_total + parts_total
        payment = OrderPayment(
            order_id=order.id,
            amount=total_amount,
            payment_method="cash",
            status="completed",
        )
        session.add(payment)
        
        transaction = CashTransaction(
            shift_id=shift.id,
            amount=total_amount,
            transaction_type=TransactionType.income,
            description=f"Оплата заказа #{order.id}",
            order_id=order.id,
            created_by=elena.id,
        )
        session.add(transaction)
        session.commit()
        
        total_revenue += total_amount
        print(f"    💵 Оплачено: {total_amount}₽")
        
        # 9. Выдан
        order.status = "issued"
        session.add(order)
        session.commit()
        print(f"    📤 Выдан")
        
        # 10. Начисляем зарплату (40% от стоимости работ)
        salary = int(service_total * 0.4)
        salary_record = SalaryRecord(
            user_id=master.id,
            order_id=order.id,
            calculated_amount=salary,
            status="accrued",
            period_start=datetime.now().replace(day=1),
            period_end=datetime.now().replace(day=15) if datetime.now().day < 15 else datetime.now(),
            comment=f"Зарплата по заказу #{order.id}",
        )
        session.add(salary_record)
        session.commit()
        
        total_salary += salary
        print(f"    💰 Зарплата мастеру {master.username}: {salary}₽")
    
    # Закрываем смену
    shift.is_open = False
    shift.closed_at = datetime.now()
    shift.final_amount = total_revenue
    session.add(shift)
    session.commit()
    print(f"\n💰 Закрыта смена #{shift.id}")
    
    # Итоги
    print("\n" + "="*70)
    print("✅ СИМУЛЯЦИЯ ЗАВЕРШЕНА!")
    print("="*70)
    print(f"\n📊 ИТОГИ:")
    print(f"  📦 Заказов: {len(orders)}")
    print(f"  💵 Выручка: {total_revenue}₽")
    print(f"  💰 Зарплата: {total_salary}₽")
    print(f"  👥 Мастеров задействовано: {len(set(o['master'].id for o in orders))}")
    print(f"  📅 Смен: 1")
    print("="*70)


if __name__ == "__main__":
    main()
