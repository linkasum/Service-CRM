from core.database import engine
from sqlmodel import Session, text
from routes.salary_assignment import auto_assign_salary
from models.user import User

with Session(engine) as s:
    alesya = s.get(User, 7)
    elena = s.get(User, 2)

    # All orders data
    orders_raw = [
        # June 3 - shift 27, Alesya
        (10044, 'Клиент 2500', '89000010044', 'Apple', 'iPhone11', 'phone', 'Экран', 4, 2500, False, 27, 'cash'),
        (10077, 'Клиент 2100', '89000010077', 'Samsung', 'A35', 'phone', 'Динамик', 3, 2100, False, 27, 'card'),
        (10065, 'Клиент 1900', '89000010065', 'Xiaomi', 'Redmi12', 'phone', 'Кнопка', 13, 1900, False, 27, 'cash'),
        (9998, 'Клиент 12000', '89000009998', 'Apple', 'MacBook', 'laptop', 'Греется', 3, 12000, False, 27, 'card'),
        (10119, 'Клиент 1500', '89000010119', 'Honor', '90', 'phone', 'Связь', 4, 1500, False, 27, 'card'),
        (10021, 'Запчасть 1400', '89000010021', '-', '-', '-', 'покупка запчасти', 3, 1400, True, 27, 'cash'),
        (10070, 'Запчасть 6400', '89000010070', '-', '-', '-', 'покупка запчасти', 3, 6400, True, 27, 'cash'),
        (10033, 'Клиент 7400', '89000010033', 'Samsung', 'S24', 'phone', 'Камера', 3, 7400, False, 27, 'card'),
        (10085, 'Клиент 1500', '89000010085', 'Apple', 'iPad', 'tablet', 'Батарея', 13, 1500, False, 27, 'card'),
        (10111, 'Клиент 2300', '89000010111', 'Huawei', 'P50', 'phone', 'WiFi', 3, 2300, False, 27, 'card'),
        (10099, 'Клиент 1500', '89000010099', 'Xiaomi', '13T', 'phone', 'Зарядка', 4, 1500, False, 27, 'cash'),
        # June 4 - shift 28, Elena
        (10140, 'Запчасть 1300', '89000010140', '-', '-', '-', 'запчасти', 4, 1300, True, 28, 'cash'),
        (10020, 'Запчасть 1400/2550', '89000010020', '-', '-', '-', 'запчасти', 6, 3950, True, 28, 'cash'),  # combined: 1400 + 2550
        (10053, 'Клиент 4400', '89000010053', 'Samsung', 'A15', 'phone', 'Корпус', 4, 4400, False, 28, 'card'),
        (10089, 'Клиент 2600', '89000010089', 'Apple', 'iPhone13', 'phone', 'Стекло', 3, 2600, False, 28, 'card'),
        (10096, 'Клиент 5700', '89000010096', 'Honor', 'Magic', 'phone', 'Влага', 6, 5700, False, 28, 'card'),
        (10118, 'Клиент 2500', '89000010118', 'Xiaomi', 'Poco', 'phone', 'Кнопки', 13, 2500, False, 28, 'cash'),
        # June 5 - shift 29, Elena
        (10074, 'Клиент 4500', '89000010074', 'Apple', 'iPhone14', 'phone', 'Батарея', 3, 4500, False, 29, 'cash'),
        (9516, 'Запчасть 940', '89000009516', '-', '-', '-', 'запчасти', 4, 940, True, 29, 'cash'),
        (10108, 'Клиент 1000', '89000010108', 'Samsung', 'S22', 'phone', 'Динамик', 4, 1000, False, 29, 'card'),
        (10127, 'Клиент 2400', '89000010127', 'Huawei', 'Nova', 'phone', 'Экран', 13, 2400, False, 29, 'card'),
        (10137, 'Клиент 2300', '89000010137', 'Apple', 'Watch', 'watch', 'Ремешок', 3, 2300, False, 29, 'card'),
        # June 6 - shift 30, Elena
        (10086, 'Клиент 2500', '89000010086', 'Xiaomi', 'Mi12', 'phone', 'Зарядка', 4, 2500, False, 30, 'card'),
        (9758, 'Клиент 2200', '89000009758', 'Samsung', 'A54', 'phone', 'Камера', 3, 2200, False, 30, 'card'),
        (10075, 'Клиент 2300', '89000010075', 'Apple', 'iPhone15', 'phone', 'Связь', 4, 2300, False, 30, 'cash'),
        (10106, 'Клиент 1500', '89000010106', 'Honor', 'X8', 'phone', 'Кнопка', 13, 1500, False, 30, 'card'),
        (10030, 'Клиент 5500', '89000010030', 'Samsung', 'S23', 'phone', 'Не включ', 3, 5500, False, 30, 'mixed'),  # 2000 cash + 3500 card
        (10126, 'Клиент 8400', '89000010126', 'Apple', 'MacBook', 'laptop', 'Греется', 3, 8400, False, 30, 'card'),
    ]

    # Delete and recreate
    for oid, name, phone, brand, model, cat, complaint, master, cost, is_parts, shift_id, pay_method in orders_raw:
        for t in ['order_comments', 'salary_records', 'order_payments', 'order_services', 'order_parts', 'cash_transactions']:
            s.execute(text(f"DELETE FROM {t} WHERE order_id={oid}"))
        s.execute(text(f"DELETE FROM orders WHERE id={oid}"))
        s.commit()
        
        status = 'repair' if is_parts else 'issued'
        paid = 0 if is_parts else cost
        acceptor_id = 7 if shift_id in (27,) else 2
        acceptor_name = 'Алеся' if shift_id in (27,) else 'Елена'
        
        s.execute(text(f"""
            INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, parts_cost, paid_amount, acceptor_id, manager_name, created_at, issued_at)
            VALUES ({oid}, '{name}', '{phone}', '{brand}', '{model}', '{cat}', '{complaint}', '{status}', {master}, {cost}, {cost if not is_parts else 0}, {cost if is_parts else 0}, {paid}, {acceptor_id}, '{acceptor_name}', '2026-06-0{shift_id-24} 10:00:00', '2026-06-0{shift_id-24} 16:00:00')
        """))

        if not is_parts:
            s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES ({oid}, 'Ремонт', {cost}, 1)"))
            method = 'card' if pay_method in ('card', 'mixed') else 'cash'
            s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES ({oid}, 'final', {cost}, '{method}', 'completed', 'Оплата #{oid}', {acceptor_id}, now())"))
        s.commit()

    # Transactions and salary
    print("=== ORDERS ===")
    for oid, name, _, _, _, _, _, master, cost, is_parts, shift_id, pay_method in orders_raw:
        user = alesya if shift_id == 27 else elena
        if not is_parts:
            # Salary
            try:
                result = auto_assign_salary(order_id=oid, session=s, current_user=user)
                sz = result.get('salary_amount', 0)
            except:
                sz = 0

            # Transactions
            if pay_method == 'cash':
                s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES ({shift_id}, {oid}, 'income', 'cash', {cost}, 'Заказ #{oid}', {user.id}, '2026-06-0{shift_id-24} 15:00:00')"))
                print(f"  #{oid}: {cost}₽ НАЛ → master={master}, зп={sz}")
            elif pay_method == 'card':
                s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES ({shift_id}, {oid}, 'income', 'card', {cost}, 'Заказ #{oid}', {user.id}, '2026-06-0{shift_id-24} 15:00:00')"))
                print(f"  #{oid}: {cost}₽ КАРТА → master={master}, зп={sz}")
            elif pay_method == 'mixed':
                s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES ({shift_id}, {oid}, 'income', 'cash', 2000, 'Заказ #{oid} (нал)', {user.id}, '2026-06-06 15:00:00')"))
                s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES ({shift_id}, {oid}, 'income', 'card', 3500, 'Заказ #{oid} (карта)', {user.id}, '2026-06-06 15:00:00')"))
                print(f"  #{oid}: 2000₽ НАЛ + 3500₽ КАРТА → master={master}, зп={sz}")
        else:
            s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES ({shift_id}, {oid}, 'expense', 'cash', -{cost}, 'Заказ #{oid} — запчасти', {user.id}, '2026-06-0{shift_id-24} 15:00:00')"))
            print(f"  #{oid}: -{cost}₽ РАСХОД (запчасти) → master={master}")
        s.commit()

    # Elena salary: 3 shifts x 4000
    for shift_num, shift_id, day in [(4, 28, '2026-06-04'), (5, 29, '2026-06-05'), (6, 30, '2026-06-06')]:
        s.execute(text(f"""
            INSERT INTO salary_records (user_id, calculated_amount, status, period_start, period_end, comment)
            VALUES (2, 4000, 'accrued', '{day} 09:00:00', '{day} 18:00:00', 'shift_auto | Смена #{shift_id} ({day})')
        """))
        s.execute(text(f"""
            INSERT INTO order_comments (order_id, user_id, username, role_name, text, is_system, created_at)
            VALUES (0, 2, 'elena', 'acceptor', 'Начислена ЗП 4000₽ за смену #{shift_id}', true, '{day} 15:00:00')
        """))
        print(f"  Elena salary: +4000₽ shift #{shift_id} ({day})")
    
    # Elena took all 12000 on June 6
    s.execute(text(f"""
        INSERT INTO cash_transactions (shift_id, transaction_type, payment_method, amount, comment, created_by, created_at)
        VALUES (30, 'expense', 'cash', -12000, 'ЗП Елены за 3 смены', 2, '2026-06-06 15:00:00')
    """))
    s.commit()
    print("  Elena took 12000₽ salary (expense, shift 30)")

    print("\n=== PARTS ORDERS (NOT CLOSED) ===")
    for oid, name, _, _, _, _, _, master, cost, is_parts, _, _ in orders_raw:
        if is_parts:
            print(f"  #{oid}: {cost}₽ | master={master} | {name}")

    print("\n=== VERIFY ===")
    for sid in [27,28,29,30]:
        txs = s.execute(text(f"SELECT payment_method, sum(amount)::int FROM cash_transactions WHERE shift_id={sid} GROUP BY payment_method ORDER BY payment_method")).fetchall()
        print(f"  Shift {sid}: {txs}")
