"""
Финальная чистка справочников
Исправляет точечные проблемы: точки, запятые, дефисы
Использование:
    cd backend
    source venv/bin/activate
    python scripts/final_cleanup.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.category import Category
from models.brand import Brand
from models.order import Order


def cleanup_categories():
    """Чистка категорий"""
    print("\n🧹 Чистка категорий...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        all_cats = session.exec(select(Category)).all()
        changes = []
        
        for cat in all_cats:
            name = cat.name
            new_name = None
            
            # Точки в конце
            if name.endswith('.') and len(name) > 3:
                base = name.rstrip('.')
                # Проверяем есть ли такая же без точки
                if any(c.name == base for c in all_cats):
                    new_name = base
                    changes.append(('Категория', name, base))
                    session.delete(cat)
                    continue
            
            # Запятые в конце
            if name.endswith(',') and len(name) > 3:
                base = name.rstrip(',').strip()
                if any(c.name == base for c in all_cats):
                    new_name = base
                    changes.append(('Категория', name, base))
                    session.delete(cat)
                    continue
        
        session.commit()
        
        print(f"\n✅ Удалено дубликатов: {len(changes)}")
        for type_, old, new in changes:
            print(f"   ❌ '{old}' → '{new}'")
        
        remaining = session.exec(select(Category)).all()
        print(f"📊 Осталось категорий: {len(remaining)}")
        
        return changes


def cleanup_brands():
    """Чистка брендов"""
    print("\n🧹 Чистка брендов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        all_brands = session.exec(select(Brand)).all()
        changes = []
        
        # Группируем по нормализованным названиям
        normalized = {}
        for brand in all_brands:
            # Нормализуем: убираем дефисы, приводим к lower
            norm = brand.name.lower().replace('-', ' ').replace('/', ' ').strip()
            if norm not in normalized:
                normalized[norm] = []
            normalized[norm].append(brand)
        
        # Находим дубликаты
        for norm, brands in normalized.items():
            if len(brands) > 1:
                # Оставляем первый (с наименьшим ID)
                main_brand = min(brands, key=lambda b: b.id)
                for brand in brands:
                    if brand.id != main_brand.id:
                        changes.append(('Бренд', brand.name, main_brand.name))
                        session.delete(brand)
                        print(f"   ❌ '{brand.name}' → '{main_brand.name}'")
        
        session.commit()
        
        print(f"\n✅ Удалено дубликатов: {len(changes)}")
        
        remaining = session.exec(select(Brand)).all()
        print(f"📊 Осталось брендов: {len(remaining)}")
        
        return changes


def update_orders():
    """Обновление заказов с нормализованными названиями"""
    print("\n🔄 Обновление заказов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        orders = session.exec(select(Order)).all()
        updated = 0
        
        for order in orders:
            changed = False
            
            # Убираем точки и запятые в конце
            if order.device_category:
                cat = order.device_category.rstrip('.').rstrip(',').strip()
                if cat != order.device_category:
                    order.device_category = cat
                    changed = True
            
            if order.device_brand:
                brand = order.device_brand.rstrip('.').rstrip(',').strip()
                if brand != order.device_brand:
                    order.device_brand = brand
                    changed = True
            
            if changed:
                updated += 1
                session.add(order)
        
        if updated > 0:
            session.commit()
            print(f"✅ Обновлён {updated} заказ(ов)")
        else:
            print("✅ Заказы не требуют обновления")


if __name__ == "__main__":
    print("=" * 70)
    print("🧹 Финальная чистка справочников")
    print("=" * 70)
    
    update_orders()
    cat_changes = cleanup_categories()
    brand_changes = cleanup_brands()
    
    print("\n" + "=" * 70)
    print("✅ Финальная чистка завершена!")
    print(f"📊 Всего изменений: {len(cat_changes) + len(brand_changes)}")
    print("=" * 70)
