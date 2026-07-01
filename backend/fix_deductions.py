from core.database import engine
from sqlmodel import Session, text
from datetime import datetime

with Session(engine) as s:

    # 1. Check current negative salary
    neg = s.execute(text("SELECT sr.order_id, u.username, sr.calculated_amount FROM salary_records sr JOIN users u ON sr.user_id = u.id WHERE sr.calculated_amount < 0")).fetchall()
    print("=== NEGATIVE SALARY (current) ===")
    for r in neg: print(f"  Order {r[0]}: {r[1]} {r[2]}")

    # 2. Check order_parts
    parts = s.execute(text("SELECT op.order_id, op.price_at_order, op.master_id, u.username FROM order_parts op LEFT JOIN users u ON op.master_id = u.id ORDER BY op.order_id")).fetchall()
    print("\n=== ORDER PARTS (need deductions) ===")
    for p in parts: print(f"  Order {p[0]}: {p[1]} -> master {p[3]} (id={p[2]})")

    # 3. Elena salary
    zp = s.execute(text("SELECT sum(calculated_amount) FROM salary_records WHERE user_id=2 AND status='accrued'")).fetchone()
    print(f"\n=== ELENA accrued: {zp[0]} ===")

    # 4. Deduct Elena's taken salary (12000 from shift 30)
    print("\n=== Deducting Elena 12000 ===")
    s.execute(text("""
        INSERT INTO salary_records (user_id, calculated_amount, status, period_start, period_end, comment, created_at)
        VALUES (2, -12000, 'deducted', '2026-06-06 09:00', '2026-06-06 18:00', 'Выплата ЗП за смены #28-30', now())
    """))
    s.commit()
    print("  Elena: -12000 deducted")

    # 5. Create deductions for parts used by masters
    print("\n=== Creating parts deductions for masters ===")
    for p in parts:
        oid, price, master_id, username = p
        if master_id and price > 0:
            # Check if deduction already exists
            exist = s.execute(text(f"SELECT id FROM salary_records WHERE order_id={oid} AND user_id={master_id} AND calculated_amount < 0")).fetchone()
            if exist:
                print(f"  Order {oid}: already has deduction for {username}")
                continue
            s.execute(text(f"""
                INSERT INTO salary_records (user_id, order_id, calculated_amount, status, period_start, period_end, comment, created_at)
                VALUES ({master_id}, {oid}, -{price}, 'deducted', now(), now(), 'Списание запчасти на заказ #{oid}', now())
            """))
            s.commit()
            print(f"  Order {oid}: -{price} deducted from {username}")

    # 6. Add "ячейки" to warehouse (100 pcs, 12600 total)
    print("\n=== Adding 'Ячейки' to warehouse ===")
    part_exists = s.execute(text("SELECT id, quantity FROM parts WHERE name='Ячейка хранения'")).fetchone()
    if not part_exists:
        s.execute(text("""
            INSERT INTO parts (name, quantity, purchase_price, sale_price, is_active)
            VALUES ('Ячейка хранения', 100, 126, 126, true)
        """))
        s.commit()
        print("  Created: Ячейка хранения, 100шт, цена 126₽/шт")
    else:
        pid, qty = part_exists
        s.execute(text(f"UPDATE parts SET quantity = quantity + 100 WHERE id={pid}"))
        s.commit()
        print(f"  Updated: +100шт, total now {qty+100}")

    # 7. Update order #10074 return — already has -4500 in transactions
    # Mark the order as returned/refunded
    s.execute(text("UPDATE orders SET status='issued', paid_amount=0 WHERE id=10074"))
    # The refund is already in cash_transactions as expense, no need to create order_payment for return

    # 8. Final checks
    print("\n=== FINAL ===")
    zp2 = s.execute(text("SELECT sum(calculated_amount) FROM salary_records WHERE user_id=2")).fetchone()
    print(f"  Elena total ZP: {zp2[0]}")
    
    neg2 = s.execute(text("SELECT count(*) FROM salary_records WHERE calculated_amount < 0")).fetchone()
    print(f"  Total deduction records: {neg2[0]}")
    
    # Total оборот check
    income = s.execute(text("SELECT payment_method, sum(amount)::int FROM cash_transactions WHERE transaction_type='income' GROUP BY payment_method")).fetchall()
    print(f"  Income: {income}")
