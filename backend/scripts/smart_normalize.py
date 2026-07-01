"""
Скрипт умной нормализации категорий и брендов
Объединяет похожие названия по правилам
Использование:
    cd backend
    source venv/bin/activate
    python scripts/smart_normalize.py
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.category import Category
from models.brand import Brand
from models.order import Order


# Правила нормализации для категорий
CATEGORY_RULES = {
    # Роботы пылесосы
    r'робот[\s-]*пылесос.*': 'Робот-пылесос',
    r'робот-пылесос.*': 'Робот-пылесос',
    r'^робот$': 'Робот-пылесос',
    r'^роботы$': 'Робот-пылесос',
    
    # Пылесосы
    r'вертикальный[\s-]*пылесос.*': 'Вертикальный пылесос',
    r'пылесос.*вертикальный.*': 'Вертикальный пылесос',
    r'^пылесос\.?$': 'Пылесос проводной',
    r'^пылес$': 'Пылесос проводной',
    r'пылесос.*проводной.*': 'Пылесос проводной',
    r'проводной[\s-]*пылесос.*': 'Пылесос проводной',
    
    # СВЧ
    r'свч.*': 'Микроволновая печь',
    r'микроволновк.*': 'Микроволновая печь',
    r'микроволнов.*печ.*': 'Микроволновая печь',
    
    # Телевизоры
    r'телевизор.*': 'Телевизор',
    r'телевезор.*': 'Телевизор',
    r'телевзор.*': 'Телевизор',
    r'телевиизор.*': 'Телевизор',
    r'тв.*': 'Телевизор',
    
    # Смартфоны
    r'смартфон.*': 'Смартфон',
    r'телефон.*': 'Смартфон',
    r'мобильный.*': 'Смартфон',
    
    # Ноутбуки
    r'ноутбук.*': 'Ноутбук',
    r'лаптоп.*': 'Ноутбук',
    
    # Планшеты
    r'планшет.*': 'Планшет',
    
    # Колонки
    r'колонк.*': 'Колонка',
    r'акустическ.*систем.*': 'Колонка',
    
    # Наушники
    r'наушник.*': 'Наушники',
    
    # Зарядные устройства
    r'зу.*': 'Зарядное устройство',
    r'зарядн.*устройств.*': 'Зарядное устройство',
    r'зарядк.*': 'Зарядное устройство',
    
    # Аккумуляторы
    r'акб.*': 'Аккумулятор',
    r'батаре[ия].*': 'Аккумулятор',
    r'аккум.*': 'Аккумулятор',
    r'акамулятор.*': 'Аккумулятор',
    r'акумулятор.*': 'Аккумулятор',
    
    # Самокаты
    r'самокат.*': 'Электросамокат',
    r'гироскутер.*': 'Гироскутер',
    
    # Кофемашины
    r'кофемаши.*': 'Кофемашина',
    r'кофемашнина.*': 'Кофемашина',
    r'кофеварк.*': 'Кофемашина',
    
    # Фены
    r'фен.*': 'Фен',
    
    # Утюги
    r'утюг.*': 'Утюг',
    r'парогенератор.*': 'Парогенератор',
    r'отпариват.*': 'Отпариватель',
    
    # Стиральные машины
    r'стиральн.*': 'Стиральная машина',
    
    # Холодильники
    r'холодильн.*': 'Холодильник',
    r'морозильн.*': 'Морозильник',
    r'автохолод.*': 'Автохолодильник',
    r'автоходол.*': 'Автохолодильник',
    
    # Кондиционеры
    r'кондиционер.*': 'Кондиционер',
    r'сплит-систем.*': 'Кондиционер',

    # Усилители
    r'усилител[еь].*': 'Усилитель',
    r'усилитель.*': 'Усилитель',
    r'усилитедь.*': 'Усилитель',
    r'аудиоусилитель.*': 'Усилитель',
    r'^усилитель.*': 'Усилитель',

    # Ресиверы
    r'ресивер.*': 'Ресивер',
    r'аудиоресивер.*': 'Ресивер',

    # Видеоигры
    r'игров.*консол.*': 'Игровая консоль',
    r'приставк.*': 'Игровая консоль',
    r'playstation.*': 'PlayStation',
    r'xbox.*': 'Xbox',
    r'nintendo.*': 'Nintendo',

    # Видеотехника
    r'видеокамер.*': 'Видеокамера',
    r'видеокарт.*': 'Видеокарта',
    r'видеомагнитофон.*': 'Видеомагнитофон',
    r'виеомагнитофон.*': 'Видеомагнитофон',
    r'видеонян[яь].*': 'Видеоняня',
    r'видеорегистратор.*': 'Видеорегистратор',
    r'регистратор.*видеонаблюдени.*': 'Видеорегистратор',
    r'видеонаблюдени.*': 'Видеонаблюдение',
}

# Правила нормализации для брендов
BRAND_RULES = {
    # Apple
    r'^apple$': 'Apple',
    r'^iphone$': 'Apple',
    r'^ipad$': 'Apple',
    r'^ipod$': 'Apple',
    
    # Samsung
    r'^samsung$': 'Samsung',
    
    # Xiaomi
    r'^xiaomi$': 'Xiaomi',
    r'^mi$': 'Xiaomi',
    r'^redmi$': 'Xiaomi',
    r'^poco$': 'Xiaomi',
    
    # Dyson
    r'^dyson$': 'Dyson',
    
    # Bosch
    r'^bosch$': 'Bosch',
    
    # Philips
    r'^philips$': 'Philips',
    
    # Sony
    r'^sony$': 'Sony',
    
    # LG
    r'^lg$': 'LG',
    
    # Braun
    r'^braun$': 'Braun',
    r'^braupunkt$': 'Braun',
    
    # DeLonghi
    r'^delonghi$': 'DeLonghi',
    r'^delongi$': 'DeLonghi',
    r'^de longhi$': 'DeLonghi',
    r'^delonghi caffe$': 'DeLonghi',
    
    # Tefal
    r'^tefal$': 'Tefal',
    r'^rowenta$': 'Tefal',
    r'^roventa$': 'Tefal',
    
    # Kärcher
    r'^karcher$': 'Kärcher',
    r'^kercher$': 'Kärcher',
    
    # Hyundai
    r'^hyundai$': 'Hyundai',
    r'^huyndai$': 'Hyundai',
    r'^hyndai$': 'Hyundai',
    r'^hynday$': 'Hyundai',
    
    # Polaris
    r'^polaris$': 'Polaris',
    
    # Redmond
    r'^redmond$': 'Redmond',
    r'^рэдредмонд$': 'Redmond',
    
    # Scarlett
    r'^scarlett$': 'Scarlett',
    r'^scarlet$': 'Scarlett',
    
    # Supra
    r'^supra$': 'Supra',
    
    # Electrolux
    r'^electrolux$': 'Electrolux',
    
    # Bork
    r'^bork$': 'Bork',
    
    # Razer
    r'^razer$': 'Razer',
    
    # Logitech
    r'^logitech$': 'Logitech',
    r'^logi$': 'Logitech',
    
    # HyperX
    r'^hyperx$': 'HyperX',
    
    # JBL
    r'^jbl$': 'JBL',
    
    # Sennheiser
    r'^sennheiser$': 'Sennheiser',
    r'^senneiser$': 'Sennheiser',
    
    # Яндекс
    r'^яндекс$': 'Яндекс',
    r'^яндекс\.? станция$': 'Яндекс',
    r'^яндекс алиса$': 'Яндекс',
    r'^алиса$': 'Яндекс',
    
    # Segway/Ninebot
    r'^ninebot$': 'Ninebot',
    r'^segway$': 'Segway',
    
    # iRobot
    r'^roomba$': 'iRobot',
    r'^irobot$': 'iRobot',
    
    # Roborock
    r'^roborock$': 'Roborock',
    
    # Xiaomi vacuum
    r'^mi robot vacuum.*': 'Xiaomi',
    r'^xiaomi robot.*': 'Xiaomi',
    r'^dreame$': 'Xiaomi',
    r'^viomi$': 'Xiaomi',
    
    # Мелкие исправления
    r'^noname$': 'NoName',
    r'^no name$': 'NoName',
    r'^noname$': 'NoName',
    r'^без бренда$': 'NoName',
    r'^без имени$': 'NoName',
}


def apply_rules(name: str, rules: Dict[str, str]) -> str:
    """Применить правила к названию"""
    name_lower = name.lower().strip()
    
    for pattern, replacement in rules.items():
        if re.match(pattern, name_lower, re.IGNORECASE):
            return replacement
    
    # Если не нашли совпадений - нормализуем базово
    return ' '.join(name.split()).title()


def find_similar(name: str, existing: List[str], threshold: float = 0.8) -> str:
    """Найти похожее название в списке"""
    import difflib
    
    name_norm = ' '.join(name.lower().split())
    matches = difflib.get_close_matches(name_norm, [n.lower() for n in existing], n=1, cutoff=threshold)
    
    if matches:
        # Возвращаем оригинальное написание из списка
        for n in existing:
            if n.lower() == matches[0]:
                return n
    
    return name


def smart_normalize_categories():
    """Умная нормализация категорий"""
    print("\n📂 Умная нормализация категорий...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        all_categories = session.exec(select(Category)).all()
        existing_names = [c.name for c in all_categories]
        
        # Считаем статистику
        stats = {"renamed": 0, "merged": 0}
        
        for cat in all_categories:
            # Применяем правила
            new_name = apply_rules(cat.name, CATEGORY_RULES)
            
            if new_name != cat.name:
                # Проверяем нет ли уже такой категории
                existing = session.exec(
                    select(Category).where(Category.name.ilike(new_name))
                ).first()
                
                if existing:
                    print(f"  🔀 '{cat.name}' → '{existing.name}' (объединение)")
                    stats["merged"] += 1
                    session.delete(cat)
                else:
                    print(f"  ✏️ '{cat.name}' → '{new_name}'")
                    cat.name = new_name
                    stats["renamed"] += 1
        
        session.commit()
        
        remaining = session.exec(select(Category)).all()
        print(f"\n✅ Переименовано: {stats['renamed']}, Объединено: {stats['merged']}")
        print(f"📊 Всего категорий: {len(remaining)}")


def smart_normalize_brands():
    """Умная нормализация брендов"""
    print("\n📂 Умная нормализация брендов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        all_brands = session.exec(select(Brand)).all()
        existing_names = [b.name for b in all_brands]
        
        stats = {"renamed": 0, "merged": 0}
        
        for brand in all_brands:
            # Применяем правила
            new_name = apply_rules(brand.name, BRAND_RULES)
            
            if new_name != brand.name:
                # Проверяем нет ли уже такого бренда
                existing = session.exec(
                    select(Brand).where(Brand.name.ilike(new_name))
                ).first()
                
                if existing:
                    print(f"  🔀 '{brand.name}' → '{existing.name}' (объединение)")
                    stats["merged"] += 1
                    session.delete(brand)
                else:
                    print(f"  ✏️ '{brand.name}' → '{new_name}'")
                    brand.name = new_name
                    stats["renamed"] += 1
        
        session.commit()
        
        remaining = session.exec(select(Brand)).all()
        print(f"\n✅ Переименовано: {stats['renamed']}, Объединено: {stats['merged']}")
        print(f"📊 Всего брендов: {len(remaining)}")


def update_orders_names():
    """Обновление названий в заказах"""
    print("\n🔄 Обновление заказов...")
    
    with engine.connect() as conn:
        session = Session(conn)
        orders = session.exec(select(Order)).all()
        
        updated = 0
        for order in orders:
            changed = False
            
            if order.device_category:
                new_cat = apply_rules(order.device_category, CATEGORY_RULES)
                if new_cat != order.device_category:
                    order.device_category = new_cat
                    changed = True
            
            if order.device_brand:
                new_brand = apply_rules(order.device_brand, BRAND_RULES)
                if new_brand != order.device_brand:
                    order.device_brand = new_brand
                    changed = True
            
            if changed:
                updated += 1
                session.add(order)
        
        if updated > 0:
            session.commit()
            print(f"✅ Обновлён {updated} заказ(ов)")


if __name__ == "__main__":
    print("=" * 70)
    print("🧠 Умная нормализация справочников")
    print("=" * 70)
    
    update_orders_names()
    smart_normalize_categories()
    smart_normalize_brands()
    
    print("\n" + "=" * 70)
    print("✅ Умная нормализация завершена!")
    print("=" * 70)
