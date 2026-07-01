"""
Скрипт нормализации категорий и брендов
Объединяет дубликаты и приводит названия к единому виду
Использование:
    cd backend
    source venv/bin/activate
    python scripts/normalize_catalog.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

# Добавляем корень backend в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select, update
from core.database import engine
from models.category import Category
from models.brand import Brand
from models.order import Order


def normalize_name(name: str) -> str:
    """
    Нормализация названия:
    - Убираем лишние пробелы
    - Приводим к правильному регистру
    - Заменяем похожие символы
    """
    if not name:
        return ""
    
    # Убираем лишние пробелы
    name = ' '.join(name.split())
    
    # Приводим к Title Case (первая заглавная)
    name = name.strip().title()
    
    # Заменяем дефисы с пробелами на дефисы без пробелов
    name = name.replace(' - ', '-').replace(' -', '-').replace('- ', '-')
    
    return name


def get_canonical_name(name: str, canonical_map: Dict[str, str]) -> str:
    """Получить каноническое название из мапы"""
    normalized = normalize_name(name)
    return canonical_map.get(normalized.lower(), normalized)


def normalize_categories():
    """Нормализация категорий"""
    print("\n📂 Нормализация категорий...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # Получаем все категории
        all_categories = session.exec(select(Category)).all()
        
        # Группируем по нормализованным названиям
        normalized_groups: Dict[str, List[Category]] = {}
        for cat in all_categories:
            norm = normalize_name(cat.name)
            if norm:
                key = norm.lower()
                if key not in normalized_groups:
                    normalized_groups[key] = []
                normalized_groups[key].append(cat)
        
        # Мапа для переименования
        rename_map = {}
        
        for norm_key, categories in normalized_groups.items():
            if len(categories) > 1:
                # Оставляем первую (с наименьшим ID), остальные помечаем на удаление
                main_cat = min(categories, key=lambda c: c.id)
                print(f"\n  📁 Группа '{norm_key}' ({len(categories)} шт):")
                print(f"     ✅ Оставляем: '{main_cat.name}' (ID={main_cat.id})")
                
                for cat in categories:
                    if cat.id != main_cat.id:
                        print(f"     ❌ Удаляем: '{cat.name}' (ID={cat.id})")
                        session.delete(cat)
        
        session.commit()
        
        # Считаем результат
        remaining = session.exec(select(Category)).all()
        print(f"\n✅ Категорий после чистки: {len(remaining)}")


def normalize_brands():
    """Нормализация брендов"""
    print("\n📂 Нормализация брендов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # Получаем все бренды
        all_brands = session.exec(select(Brand)).all()
        
        # Группируем по нормализованным названиям
        normalized_groups: Dict[str, List[Brand]] = {}
        for brand in all_brands:
            norm = normalize_name(brand.name)
            if norm:
                key = norm.lower()
                if key not in normalized_groups:
                    normalized_groups[key] = []
                normalized_groups[key].append(brand)
        
        for norm_key, brands in normalized_groups.items():
            if len(brands) > 1:
                # Оставляем первую (с наименьшим ID)
                main_brand = min(brands, key=lambda b: b.id)
                print(f"\n  🏷️ Группа '{norm_key}' ({len(brands)} шт):")
                print(f"     ✅ Оставляем: '{main_brand.name}' (ID={main_brand.id})")
                
                for brand in brands:
                    if brand.id != main_brand.id:
                        print(f"     ❌ Удаляем: '{brand.name}' (ID={brand.id})")
                        session.delete(brand)
        
        session.commit()
        
        # Считаем результат
        remaining = session.exec(select(Brand)).all()
        print(f"\n✅ Брендов после чистки: {len(remaining)}")


def update_orders_with_canonical_names():
    """Обновление заказов с каноническими названиями"""
    print("\n🔄 Обновление заказов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # Получаем все уникальные названия категорий и брендов из заказов
        orders = session.exec(select(Order)).all()
        
        updated_count = 0
        
        for order in orders:
            updated = False
            
            # Нормализуем категорию
            if order.device_category:
                new_cat = normalize_name(order.device_category)
                if new_cat != order.device_category:
                    order.device_category = new_cat
                    updated = True
            
            # Нормализуем бренд
            if order.device_brand:
                new_brand = normalize_name(order.device_brand)
                if new_brand != order.device_brand:
                    order.device_brand = new_brand
                    updated = True
            
            if updated:
                updated_count += 1
                session.add(order)
        
        if updated_count > 0:
            session.commit()
            print(f"✅ Обновлён {updated_count} заказ(ов)")
        else:
            print("✅ Заказы не требуют обновления")


if __name__ == "__main__":
    print("=" * 60)
    print("🧹 Нормализация справочников")
    print("=" * 60)
    
    # Сначала обновляем заказы
    update_orders_with_canonical_names()
    
    # Потом чистим категории
    normalize_categories()
    
    # Потом чистим бренды
    normalize_brands()
    
    print("\n" + "=" * 60)
    print("✅ Нормализация завершена!")
    print("=" * 60)
