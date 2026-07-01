import openpyxl
from core.database import engine
from sqlmodel import Session, text

# Read Excel
wb = openpyxl.load_workbook('/app/orders.xlsx')
ws = wb['Прибыль по заказам']

# Status mapping
STATUS_MAP = {
    'Выдан': 'issued',
    'Выдан Б.Р.': 'issued_br',
    'УТИЛЬ': 'cancelled',
    'Хранение/донор': 'cancelled',
}

# Master name → user_id
MASTER_MAP = {
    'Павел': 13, 'Евгений': 3, 'Игорь': 6, 'Николай': 4,
    'Елена': 2, 'Алеся': 7, 'Василий': None, 'Приемщик': 7,
    '': None, None: None,
}

with Session(engine) as s:
    # Get existing order IDs
    existing = set()
    for r in s.execute(text("SELECT id FROM orders")).fetchall():
        existing.add(r[0])
    print(f"Existing orders: {len(existing)}")
    
    # Parse Excel, skip header
    new_count = 0
    skip_count = 0
    batch = []
    
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True)):
        if row_idx % 500 == 0:
            print(f"  Processing row {row_idx}...")
        
        oid_str = str(row[0] or '').replace('#', '').strip()
        if not oid_str.isdigit():
            continue
        
        oid = int(oid_str)
        if oid in existing:
            skip_count += 1
            continue
        
        # Parse fields
        order_type = str(row[1] or 'Ремонт')
        status = STATUS_MAP.get(str(row[2] or ''), 'issued')
        created_at = str(row[3] or '')[:19] if row[3] else None
        closed_at = str(row[5] or '')[:19] if row[5] else None
        manager = str(row[7] or 'Приемщик')
        master_name = str(row[8] or '')
        master_id = MASTER_MAP.get(master_name)
        complaint = str(row[9] or '')
        appearance = str(row[10] or 'б/у')
        device_category = str(row[11] or '')
        serial = str(row[12] or '') if row[12] else None
        brand = str(row[13] or '')
        model = str(row[14] or '')
        accessories = str(row[15] or '') if row[15] else None
        delivery = str(row[16] or '')
        warranty = str(row[17] or '')
        legal = str(row[18] or '') if row[18] else None
        client_name = str(row[19] or '')
        client_phone = str(row[20] or '')
        client_type = str(row[21] or 'individual')
        age_group = str(row[22] or '') if row[22] else None
        source = str(row[26] or '') if row[26] else None
        service_price = str(row[27] or '') if row[27] else None
        parts_price = str(row[28] or '') if row[28] else None
        
        # Parse total cost
        total_cost = 0
        try:
            if service_price:
                total_cost += float(str(service_price).replace(',', '.').replace(' ', ''))
            if parts_price:
                total_cost += float(str(parts_price).replace(',', '.').replace(' ', ''))
        except:
            pass
        
        # Clean strings for SQL
        def esc(v):
            if v is None: return 'NULL'
            s = str(v).replace("'", "''").replace('\\', '\\\\')
            return f"'{s}'"
        
        batch.append(f"({oid}, {esc(client_name)}, {esc(client_phone)}, {esc(brand)}, {esc(model)}, {esc(device_category)}, {esc(complaint)}, '{status}', {master_id or 'NULL'}, {total_cost}, {total_cost if total_cost>0 else 'NULL'}, 0, 7, {esc(manager)}, {esc(created_at) if created_at else 'now()'}, {esc(closed_at) if closed_at else 'NULL'}, {esc(appearance)}, {esc(accessories)}, {esc(age_group)}, {esc(source)}, {esc(order_type)})")
        
        new_count += 1
        
        # Insert in batches of 200
        if len(batch) >= 200:
            sql = "INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, parts_cost, acceptor_id, manager_name, created_at, issued_at, appearance, accessories, age_group, source, order_type) VALUES " + ", ".join(batch)
            try:
                s.execute(text(sql))
                s.commit()
            except Exception as e:
                print(f"  Batch error: {e}")
                s.rollback()
            batch = []
    
    # Final batch
    if batch:
        sql = "INSERT INTO orders (id, client_name, client_phone, device_brand, device_model, device_category, complaint, status, master_id, total_cost, work_cost, parts_cost, acceptor_id, manager_name, created_at, issued_at, appearance, accessories, age_group, source, order_type) VALUES " + ", ".join(batch)
        try:
            s.execute(text(sql))
            s.commit()
        except Exception as e:
            print(f"  Final batch error: {e}")
    
    print(f"\nDone: {new_count} imported, {skip_count} skipped (already exist)")
    total = s.execute(text("SELECT count(*) FROM orders")).fetchone()[0]
    print(f"Total orders in DB: {total}")
