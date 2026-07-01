from core.database import engine
from sqlmodel import Session, text
from datetime import datetime

with Session(engine) as s:
    # Delete existing data for these new orders if needed
    new_oids = [10184,10187,10152,10198,10168,10181,10079,10192,10158,10179,10147,10203,10155,10201,10202,10171,10197,10205,10206,10213,10215,10172,10173]
    for oid in new_oids:
        for t in ['order_comments','salary_records','order_payments','order_services','order_parts','cash_transactions']:
            s.execute(text(f"DELETE FROM {t} WHERE order_id={oid}"))
        s.execute(text(f"DELETE FROM orders WHERE id={oid}"))
    
    # Create shifts 40-43
    for sid, dt, who in [(40,'2026-06-15',7),(41,'2026-06-16',2),(42,'2026-06-17',2),(43,'2026-06-18',2)]:
        s.execute(text(f"INSERT INTO cash_shifts (id, opened_at, closed_at, is_open, initial_amount, final_amount, opened_by, closed_by) VALUES ({sid}, '{dt} 09:00', '{dt} 18:00', false, 0, 0, {who}, {who}) ON CONFLICT DO NOTHING"))
    
    # ============ JUNE 15 ============
    orders_j15 = [
        (10184, 'K', '79000000000', '-', '-', '-', 'repair', 13, 1700, 'card', 'Алеся'),
        (10187, 'K', '79000000000', '-', '-', '-', 'repair', 3, 2500, 'card', 'Алеся'),
        (10152, 'K', '79000000000', '-', '-', '-', 'repair', 3, 1800, 'card', 'Алеся'),
        (10198, 'K', '79000000000', '-', '-', '-', 'repair', 4, 1000, 'cash', 'Алеся'),
        (10168, 'K', '79000000000', '-', '-', '-', 'repair', 4, 1500, 'cash', 'Алеся'),
    ]
    for oid, name, ph, br, md, ct, cm, mid, cost, method, mgr in orders_j15:
        s.execute(text(f"INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, paid_amount, acceptor_id, manager_name, created_at, issued_at) VALUES ({oid},'{name}','{ph}','{br}','{md}','{ct}','{cm}','issued',{mid},{cost},{cost},{cost},7,'{mgr}','2026-06-15 10:00','2026-06-15 12:00')"))
        s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES ({oid},'Ремонт',{cost},1)"))
        s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES ({oid},'final',{cost},'{method}','completed','#{oid}',7,now())"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (40,{oid},'income','{method}',{cost},'#{oid}',7,'2026-06-15 12:00')"))

    # Parts expense #10197
    s.execute(text(f"INSERT INTO orders (id, client_name, status, master_id, total_cost, parts_cost, acceptor_id, manager_name, created_at) VALUES (10197,'K','repair',4,1500,1500,7,'Алеся','2026-06-15 10:00') ON CONFLICT DO NOTHING"))
    s.execute(text(f"UPDATE orders SET parts_cost=1500, total_cost=1500 WHERE id=10197"))
    s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (40,10197,'expense','cash',-1500,'#10197 запчасти',7,'2026-06-15 12:00')"))

    # Cash injection +100000
    s.execute(text(f"INSERT INTO cash_transactions (shift_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (40,'income','cash',100000,'Приход (Евгений)',7,'2026-06-15 10:00')"))
    
    # Cash injection +10000
    s.execute(text(f"INSERT INTO cash_transactions (shift_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (40,'income','cash',10000,'Приход (Евгений)',7,'2026-06-15 11:00')"))

    # ZP payouts (expenses from cash)
    zp_payouts = [
        (44000, 'Алеся', 'ЗП Алеся'),
        (23000, 'Николай', 'ЗП Николай'),
        (4000, 'Николай', 'ЗП Николай смена'),
        (58000, 'Евгений', 'ЗП Евгений'),
        (11000, 'Игорь', 'ЗП Игорь'),
        (10500, 'Павел', 'ЗП Павел'),
    ]
    zps_total = 0
    for amt, who, comment in zp_payouts:
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (40,'expense','cash',-{amt},'{comment}',7,'2026-06-15 12:00')"))
        zps_total += amt
    
    # Create salary records for payouts
    zp_users = {'Алеся':7,'Николай':4,'Евгений':3,'Игорь':6,'Павел':13}
    for amt, who, comment in zp_payouts:
        uid = zp_users[who]
        s.execute(text(f"INSERT INTO salary_records (user_id, calculated_amount, status, period_start, period_end, comment, created_at) VALUES ({uid},-{amt},'paid',now(),now(),'{comment}',now())"))
    
    # ============ JUNE 16 ============
    orders_j16 = [
        (10181, 'K', 3, 1500, 'cash', 'Елена'),
        (10079, 'K', 6, 15000, 'cash', 'Елена'),
        (10192, 'K', 3, 1800, 'card', 'Елена'),
        (10158, 'K', 3, 8000, 'card', 'Елена'),
    ]
    for oid, name, mid, cost, method, mgr in orders_j16:
        s.execute(text(f"INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, paid_amount, acceptor_id, manager_name, created_at, issued_at) VALUES ({oid},'{name}','79000000000','-','-','-','repair','issued',{mid},{cost},{cost},{cost},2,'{mgr}','2026-06-16 10:00','2026-06-16 12:00') ON CONFLICT DO NOTHING"))
        s.execute(text(f"UPDATE orders SET total_cost={cost}, work_cost={cost}, paid_amount={cost}, status='issued', master_id={mid} WHERE id={oid}"))
        s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES ({oid},'Ремонт',{cost},1) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES ({oid},'final',{cost},'{method}','completed','#{oid}',2,now()) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (41,{oid},'income','{method}',{cost},'#{oid}',2,'2026-06-16 12:00')"))

    # Parts: #10213 (-1050 card), #10215 (-9500 card)
    for oid, amt in [(10213,1050),(10215,9500)]:
        s.execute(text(f"INSERT INTO orders (id, status, master_id, parts_cost, total_cost, acceptor_id, manager_name, created_at) VALUES ({oid},'repair',4,{amt},{amt},2,'Елена','2026-06-16 10:00') ON CONFLICT DO NOTHING"))
        s.execute(text(f"UPDATE orders SET parts_cost={amt}, total_cost={amt} WHERE id={oid}"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (41,{oid},'expense','card',-{amt},'#{oid} запчасти',2,'2026-06-16 12:00')"))

    # #10213 payment: 6750 cash
    s.execute(text(f"UPDATE orders SET total_cost=total_cost+6750, work_cost=6750, paid_amount=6750, status='issued' WHERE id=10213"))
    s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES (10213,'Ремонт',6750,1) ON CONFLICT DO NOTHING"))
    s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES (10213,'final',6750,'cash','completed','#10213',2,now()) ON CONFLICT DO NOTHING"))
    s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (41,10213,'income','cash',6750,'#10213',2,'2026-06-16 12:00')"))

    # ============ JUNE 17 ============
    orders_j17 = [
        (10179, 4, 1500, 'cash'),
        (10147, 13, 3000, 'card'),
        (10203, 3, 6500, 'cash'),
        (10155, 4, 11300, 'card'),
        (10201, 3, 2000, 'cash'),
    ]
    for oid, mid, cost, method in orders_j17:
        s.execute(text(f"INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, paid_amount, acceptor_id, manager_name, created_at, issued_at) VALUES ({oid},'K','790','-','-','-','repair','issued',{mid},{cost},{cost},{cost},2,'Елена','2026-06-17 10:00','2026-06-17 12:00') ON CONFLICT DO NOTHING"))
        s.execute(text(f"UPDATE orders SET total_cost={cost}, work_cost={cost}, paid_amount={cost}, status='issued', master_id={mid} WHERE id={oid}"))
        s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES ({oid},'Ремонт',{cost},1) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES ({oid},'final',{cost},'{method}','completed','#{oid}',2,now()) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (42,{oid},'income','{method}',{cost},'#{oid}',2,'2026-06-17 12:00')"))

    # Parts June 17
    parts_j17 = [(10206,2219,3),(10203,2168,3),(10205,1660,3),(10201,168,3),(10187,435,3),(10172,4250,13),(10173,1050,13)]
    for oid, amt, mid in parts_j17:
        s.execute(text(f"INSERT INTO orders (id, status, master_id, parts_cost, total_cost, acceptor_id, manager_name, created_at) VALUES ({oid},'repair',{mid},{amt},{amt},2,'Елена','2026-06-17 10:00') ON CONFLICT DO NOTHING"))
        s.execute(text(f"UPDATE orders SET parts_cost=COALESCE(parts_cost,0)+{amt}, total_cost=COALESCE(total_cost,0)+{amt} WHERE id={oid}"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (42,{oid},'expense','cash',-{amt},'#{oid} запчасти',2,'2026-06-17 12:00')"))

    # Phone expense
    s.execute(text(f"INSERT INTO cash_transactions (shift_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (42,'expense','cash',-1000,'Оплата телефона',2,'2026-06-17 12:00')"))

    # ============ JUNE 18 ============
    orders_j18 = [
        (10202, 13, 2100, 'card'),
        (10171, 13, 2100, 'card'),
        (10197, 4, 5200, 'cash'),
        (10205, 3, 6500, 'card'),
    ]
    for oid, mid, cost, method in orders_j18:
        s.execute(text(f"INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, paid_amount, acceptor_id, manager_name, created_at, issued_at) VALUES ({oid},'K','790','-','-','-','repair','issued',{mid},{cost},{cost},{cost},2,'Елена','2026-06-18 10:00','2026-06-18 12:00') ON CONFLICT DO NOTHING"))
        s.execute(text(f"UPDATE orders SET total_cost={cost}, work_cost={cost}, paid_amount={cost}, status='issued', master_id={mid} WHERE id={oid}"))
        s.execute(text(f"INSERT INTO order_services (order_id, service_name, price_at_order, quantity) VALUES ({oid},'Ремонт',{cost},1) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO order_payments (order_id, payment_type, amount, method, status, comment, created_by_id, created_at) VALUES ({oid},'final',{cost},'{method}','completed','#{oid}',2,now()) ON CONFLICT DO NOTHING"))
        s.execute(text(f"INSERT INTO cash_transactions (shift_id, order_id, transaction_type, payment_method, amount, comment, created_by, created_at) VALUES (43,{oid},'income','{method}',{cost},'#{oid}',2,'2026-06-18 12:00')"))

    s.commit()
    
    # Recalculate shifts cascade from shift 39
    prev_final = s.execute(text("SELECT final_amount FROM cash_shifts WHERE id=39")).fetchone()[0]
    print(f"Shift 39 final: {prev_final}")
    
    for sid in range(40, 44):
        s.execute(text(f"UPDATE cash_shifts SET initial_amount={prev_final} WHERE id={sid}"))
        txs = s.execute(text(f"SELECT COALESCE(sum(CASE WHEN transaction_type='income' AND payment_method='cash' THEN amount ELSE 0 END),0), COALESCE(sum(CASE WHEN transaction_type!='income' AND payment_method='cash' THEN abs(amount) ELSE 0 END),0) FROM cash_transactions WHERE shift_id={sid}")).fetchone()
        cash_in, cash_out = txs[0] or 0, txs[1] or 0
        new_final = prev_final + cash_in - cash_out
        s.execute(text(f"UPDATE cash_shifts SET final_amount={new_final} WHERE id={sid}"))
        print(f"Shift {sid}: {prev_final} + {cash_in} - {cash_out} = {new_final}")
        prev_final = new_final
    
    # Also handle #10168 payment (1500 cash, was already in repair, now issuing)
    # Already handled in orders_j15
    
    # ZP for new issued orders
    s.execute(text("""
        DELETE FROM salary_records WHERE order_id IN (10184,10187,10152,10198,10168,10181,10079,10192,10158,10213,10179,10147,10203,10155,10201,10202,10171,10197,10205)
    """))
    
    s.execute(text("""
        INSERT INTO salary_records (user_id, order_id, calculated_amount, status, period_start, period_end, comment, created_at)
        SELECT o.master_id, o.id,
          (COALESCE((SELECT sum(amount) FROM cash_transactions WHERE order_id=o.id AND transaction_type='income'),0)
           - COALESCE((SELECT sum(abs(amount)) FROM cash_transactions WHERE order_id=o.id AND transaction_type!='income'),0)) * 0.4,
          'accrued', now(), now(), 'Авто за заказ #' || o.id, now()
        FROM orders o WHERE o.id IN (10184,10187,10152,10198,10168,10181,10079,10192,10158,10213,10179,10147,10203,10155,10201,10202,10171,10197,10205)
          AND o.status='issued' AND o.master_id IS NOT NULL
          AND (COALESCE((SELECT sum(amount) FROM cash_transactions WHERE order_id=o.id AND transaction_type='income'),0)
               - COALESCE((SELECT sum(abs(amount)) FROM cash_transactions WHERE order_id=o.id AND transaction_type!='income'),0)) * 0.4 > 0
    """))
    s.commit()
    
    print("\nFinal cash chain:")
    for sid in range(39, 44):
        sh = s.execute(text(f"SELECT initial_amount, final_amount FROM cash_shifts WHERE id={sid}")).fetchone()
        print(f"  Shift {sid}: {sh[0]} -> {sh[1]}")
    
    # ZP totals
    zp = s.execute(text("""
        SELECT u.username, sum(sr.calculated_amount)::int as net
        FROM salary_records sr JOIN users u ON sr.user_id=u.id
        WHERE u.id IN (3,4,6,13) GROUP BY u.username ORDER BY net DESC
    """)).fetchall()
    print("\nZP totals (including payouts):")
    for r in zp: print(f"  {r[0]}: {r[1]}")
