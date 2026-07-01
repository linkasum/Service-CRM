"""
Чистка брендов: транслит, модели, мусор
Использование:
    cd backend
    source venv/bin/activate
    python scripts/cleanup_brands.py
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.brand import Brand
from models.order import Order


# === 1. ТРАНСЛИТ → ЛАТИНИЦА ===
# Словарь замены: что искать → чем заменить
TRANSLIT_MAP = {
    # Отдельные буквы
    'а': 'a', 'А': 'A',
    'е': 'e', 'Е': 'E',
    'о': 'o', 'О': 'O',
    'р': 'p', 'Р': 'P',
    'с': 'c', 'С': 'C',
    'т': 't', 'Т': 'T',
    'у': 'y', 'У': 'Y',
    'х': 'x', 'Х': 'X',
    'в': 'b', 'В': 'B',
    'к': 'k', 'К': 'K',
    'м': 'm', 'М': 'M',
    'н': 'n', 'Н': 'N',
    'и': 'i', 'И': 'I',
    'л': 'l', 'Л': 'L',
    'б': '6', 'Б': '6',  # Похоже на цифру
}

# Полные названия брендов с транслитом
BRAND_TRANSLATIONS = {
    'Dеlonghi': 'DeLonghi',  # кириллица 'е'
    'Dеlоnghi': 'DeLonghi',  # несколько кириллических
    'Dеlonghi Мagnificа': 'DeLonghi Magnifica',
    'Dеlonghi Мagnificа S': 'DeLonghi Magnifica S',
    'Dеlonghi Dinamica': 'DeLonghi Dinamica',
    'Dеlonghi Stirella': 'DeLonghi Stirella',
    'Makiтa': 'Makita',  # кириллица 'т'
    'Mетабо': 'Metabo',
    'Meтabo': 'Metabo',
    'Cаnоn': 'Canon',
    'Asлno': 'Asus',  # предположительно
    'Ga.Мa': 'Ga.Ma',
    'Hoboт': 'Hobot',
    'Iboтo': 'iBot',
    'Mi Roвot': 'Xiaomi',
    'Ninebot Копия': 'Ninebot',
    'Apple Копия': 'Apple',
    'Lеnovo': 'Lenovo',
    'Lеnovo G5-30': 'Lenovo',
    'Dеll': 'Dell',
    'Eлsine': 'Elsine',
    'Iоvа': 'Iova',
    'Kiтcen Aid': 'KitchenAid',
    'Lidsто': 'Lidsto',
    'Lуdsто': 'Ludsto',
    'Ckaтa': 'Skata',
    'Auтech': 'Autech',
    'Deхp': 'Dexp',
    'Ilifе': 'iLife',
    'Mamiboт': 'Mamibot',
    'Iоvа': 'Iova',
    'Liberтi': 'Liberti',
    'Angel Eуe': 'Angel Eye',
    'Accеstyle': 'Accestyle',
}


def has_cyrillic(text: str) -> bool:
    """Проверяет наличие кириллицы"""
    return bool(re.search('[а-яА-ЯёЁ]', text))


def convert_cyrillic_to_latin(text: str) -> str:
    """Конвертирует кириллические буквы в латинские"""
    result = text
    for cyrillic, latin in TRANSLIT_MAP.items():
        result = result.replace(cyrillic, latin)
    return result


def cleanup_translit(session: Session) -> List[Tuple[str, str]]:
    """Чистка транслита"""
    print("\n🔄 1. ТРАНСЛИТ → ЛАТИНИЦА")
    print("-" * 50)
    
    all_brands = session.exec(select(Brand)).all()
    changes = []
    
    for brand in all_brands:
        new_name = None
        
        # Проверяем точные совпадения
        if brand.name in BRAND_TRANSLATIONS:
            new_name = BRAND_TRANSLATIONS[brand.name]
        
        # Проверяем наличие кириллицы
        elif has_cyrillic(brand.name):
            # Пробуем сконвертировать
            converted = convert_cyrillic_to_latin(brand.name)
            # Если изменилось и не похоже на мусор
            if converted != brand.name and len(converted) >= 2:
                # Проверяем нет ли уже такого бренда
                existing = session.exec(
                    select(Brand).where(Brand.name.ilike(converted))
                ).first()
                
                if existing:
                    # Объединяем с существующим
                    new_name = existing.name
                else:
                    new_name = converted
        
        if new_name and new_name != brand.name:
            print(f"   ✏️ '{brand.name}' → '{new_name}'")
            
            # Обновляем заказы
            orders = session.exec(select(Order).where(Order.device_brand == brand.name)).all()
            for order in orders:
                order.device_brand = new_name
                session.add(order)
            
            # Проверяем дубликат
            existing = session.exec(select(Brand).where(Brand.name == new_name)).first()
            if existing:
                session.delete(brand)
            else:
                brand.name = new_name
            
            changes.append((brand.name, new_name))
    
    session.commit()
    print(f"\n✅ Изменено: {len(changes)}")
    return changes


# === 2. БРЕНДЫ С МОДЕЛЯМИ ===
# Паттерны для выделения бренда из названия
BRAND_PATTERNS = [
    # "Бренд Модель" → "Бренд"
    (r'^(Epson)\s+(L\d+)$', r'\1'),
    (r'^(Rowenta)\s+(Pro|Elite|.*\d+)$', r'\1'),
    (r'^(Kenwood)\s+(Pro.*\d+|\d+W)$', r'\1'),
    (r'^(Kugoo)\s+(S\d+.*|G\d+.*)$', r'\1'),
    (r'^(Dreame)\s+(Bot.*|L\d+.*)$', r'\1'),
    (r'^(Xiaomi)\s+(Book.*|Robot.*|Vacuum.*)$', r'\1'),
    (r'^(Redmi)\s+(Book.*|Note.*|Pro.*)$', r'\1'),
    (r'^(Realme)\s+(Buds.*|C\d+.*|GT.*)$', r'\1'),
    (r'^(Lenovo)\s+(G\d+.*|ThinkPad.*|IdeaPad.*)$', r'\1'),
    (r'^(HP)\s+(Pavilion.*|ProBook.*|EliteBook.*)$', r'\1'),
    (r'^(Dell)\s+(Inspiron.*|XPS.*|Latitude.*)$', r'\1'),
    (r'^(Asus)\s+(ROG.*|TUF.*|ZenBook.*)$', r'\1'),
    (r'^(Acer)\s+(Aspire.*|Nitro.*|Predator.*)$', r'\1'),
    (r'^(MSI)\s+(GF\d+.*|GP\d+.*|GE\d+.*)$', r'\1'),
    (r'^(LG)\s+(\d+.*|GP-B.*)$', r'\1'),
    (r'^(Samsung)\s+(Galaxy.*|Note.*|S\d+.*)$', r'\1'),
    (r'^(Sony)\s+(WH-.*|WF-.*|Xperia.*)$', r'\1'),
    (r'^(Bosch)\s+(GBH.*|GSR.*|PSR.*)$', r'\1'),
    (r'^(Makita)\s+(DF\d+.*|HR\d+.*|BHR\d+.*)$', r'\1'),
    (r'^(Metabo)\s+(BS.*|SB.*|KGS.*)$', r'\1'),
    (r'^(Philips)\s+(HR\d+.*|S\d+.*|BDS.*)$', r'\1'),
    (r'^(Dyson)\s+(V\d+.*|DC\d+.*)$', r'\1'),
    (r'^(iRobot)\s+(Roomba\s*\d+|Braava.*)$', r'\1'),
    (r'^(Roborock)\s+(S\d+.*|Q\d+.*|E\d+.*)$', r'\1'),
    (r'^(Ninebot)\s+(ES\d+.*|Max.*|F\d+.*)$', r'\1'),
    (r'^(Segway)\s+(Ninebot.*|KickScooter.*)$', r'\1'),
    (r'^(Honor)\s+(Magic.*|View.*|Play.*)$', r'\1'),
    (r'^(Huawei)\s+(P\d+.*|Mate.*|Nova.*)$', r'\1'),
    (r'^(Jabra)\s+(Talk.*|Elite.*|Evolve.*)$', r'\1'),
    (r'^(Sennheiser)\s+(HD.*|CX.*|Momentum.*)$', r'\1'),
    (r'^(Logitech)\s+(G.*|MX.*|K\d+.*)$', r'\1'),
    (r'^(Razer)\s+(DeathAdder.*|Viper.*|Basilisk.*)$', r'\1'),
    (r'^(HyperX)\s+(Cloud.*|Pulse.*|Alloy.*)$', r'\1'),
    (r'^(JBL)\s+(Flip.*|Charge.*|Go.*|Tune.*)$', r'\1'),
    (r'^(Yandex)\s+(Station.*|Alice.*)$', r'\1'),
    (r'^(Apple)\s+(iPhone.*|iPad.*|MacBook.*|Watch.*|AirPods.*)$', r'\1'),
]


def extract_brand(name: str) -> Tuple[Optional[str], Optional[str]]:
    """Извлекает бренд и модель из названия"""
    for pattern, brand_pattern in BRAND_PATTERNS:
        match = re.match(pattern, name, re.IGNORECASE)
        if match:
            brand = re.sub(brand_pattern, r'\1', name, flags=re.IGNORECASE)
            # Получаем бренд по паттерну
            brand_match = re.match(brand_pattern, name, re.IGNORECASE)
            if brand_match:
                brand = brand_match.group(1)
                # Модель - это всё что после бренда
                model = name[len(brand):].strip()
                return brand, model
    return None, None


def cleanup_brands_with_models(session: Session) -> List[Tuple[str, str, str]]:
    """Выделение моделей из названий брендов"""
    print("\n🔄 2. БРЕНДЫ С МОДЕЛЯМИ → РАЗДЕЛЕНИЕ")
    print("-" * 50)
    
    all_brands = session.exec(select(Brand)).all()
    changes = []
    
    for brand in all_brands:
        # Пропускаем короткие названия (1-2 слова без цифр)
        if len(brand.name.split()) < 2:
            continue
        
        # Пропускаем если нет цифр (скорее всего не модель)
        if not any(c.isdigit() for c in brand.name):
            continue
        
        brand_name, model = extract_brand(brand.name)
        
        if brand_name and model:
            print(f"   📦 '{brand.name}'")
            print(f"      Бренд: {brand_name}, Модель: {model}")
            
            # Проверяем есть ли уже такой бренд
            existing_brand = session.exec(
                select(Brand).where(Brand.name.ilike(brand_name))
            ).first()
            
            if existing_brand:
                # Обновляем заказы: бренд → existing_brand.name, модель → device_model
                orders = session.exec(select(Order).where(Order.device_brand == brand.name)).all()
                for order in orders:
                    order.device_brand = existing_brand.name
                    if model and not order.device_model:
                        order.device_model = model
                    session.add(order)
                
                print(f"      ✅ Обновлено заказов: {len(orders)}")
                session.delete(brand)
                changes.append((brand.name, existing_brand.name, model))
            else:
                # Создаём новый бренд
                print(f"      ℹ️ Создаём бренд '{brand_name}'")
                brand.name = brand_name
    
    session.commit()
    print(f"\n✅ Разделено: {len(changes)}")
    return changes


# === 3. МУСОРНЫЕ БРЕНДЫ ===
GARBAGE_PATTERNS = [
    r'^\d+[,\.]\d+\s*[А-Яа-яA-Za-z]*$',  # "2,0 Ач", "3.5mm"
    r'^.*\s*[-/]\s*\d+$',  # "Classic - 2"
    r'^Cordless.*',  # "Cordless Vacuum Cleaner"
    r'^Hand\s+Vacuum.*',
    r'^Lithium.*',  # "Lithium Iron Phosphate"
    r'^Smart\s+Fish.*',
    r'^.*Копия$',  # "Apple Копия"
    r'^.*\s*/\s*.*$',  # "Philips / Karcher" - разделим позже
    r'^\d+$',  # Только цифры
    r'^[A-Z]\s*\d+$',  # "H3", "G5"
]

GARBAGE_EXACT = [
    'Cordless Vacuum Cleaner',
    'Hand Vacuum Cleaner',
    'Lithium Iron Phosphate',
    'Smart Fish Feeder',
    'Angel Eуe',  # Непонятно что
    'Aviano 9',  # Слишком общее
]


def cleanup_garbage(session: Session) -> List[str]:
    """Удаление мусорных брендов"""
    print("\n🔄 3. УДАЛЕНИЕ МУСОРА")
    print("-" * 50)
    
    all_brands = session.exec(select(Brand)).all()
    deleted = []
    
    for brand in all_brands:
        is_garbage = False
        
        # Проверяем точные совпадения
        if brand.name in GARBAGE_EXACT:
            is_garbage = True
        
        # Проверяем паттерны
        for pattern in GARBAGE_PATTERNS:
            if re.match(pattern, brand.name, re.IGNORECASE):
                is_garbage = True
                break
        
        if is_garbage:
            print(f"   ❌ '{brand.name}'")
            
            # Обновляем заказы (сбрасываем бренд)
            orders = session.exec(select(Order).where(Order.device_brand == brand.name)).all()
            for order in orders:
                order.device_brand = None
                session.add(order)
            
            session.delete(brand)
            deleted.append(brand.name)
    
    session.commit()
    print(f"\n✅ Удалено: {len(deleted)}")
    return deleted


def split_combined_brands(session: Session) -> List[Tuple[str, List[str]]]:
    """Разделение комбинированных брендов типа "Philips / Karcher" """
    print("\n🔄 4. РАЗДЕЛЕНИЕ КОМБИНИРОВАННЫХ БРЕНДОВ")
    print("-" * 50)
    
    all_brands = session.exec(select(Brand)).all()
    changes = []
    
    for brand in all_brands:
        # Ищем разделители
        if ' / ' in brand.name or ', ' in brand.name or ' - ' in brand.name:
            # Разделяем
            parts = re.split(r'\s*[/,-]\s*', brand.name)
            parts = [p.strip() for p in parts if p.strip()]
            
            if len(parts) >= 2:
                print(f"   🔀 '{brand.name}' → {parts}")
                
                # Первый бренд оставляем, остальные создаём или находим
                main_brand = parts[0]
                
                # Обновляем текущий бренд
                brand.name = main_brand
                
                # Создаём остальные
                for part in parts[1:]:
                    existing = session.exec(select(Brand).where(Brand.name.ilike(part))).first()
                    if not existing:
                        new_brand = Brand(name=part, is_active=True)
                        session.add(new_brand)
                        print(f"      ➕ Создан '{part}'")
                
                changes.append((brand.name, parts))
    
    session.commit()
    print(f"\n✅ Разделено: {len(changes)}")
    return changes


if __name__ == "__main__":
    print("=" * 70)
    print("🧹 ЧИСТКА БРЕНДОВ")
    print("=" * 70)
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # 1. Транслит
        translit_changes = cleanup_translit(session)
        
        # 2. Модели
        model_changes = cleanup_brands_with_models(session)
        
        # 3. Мусор
        garbage_deleted = cleanup_garbage(session)
        
        # 4. Комбинированные
        combined_split = split_combined_brands(session)
        
        # Итоги
        print("\n" + "=" * 70)
        print("✅ ЧИСТКА ЗАВЕРШЕНА!")
        print(f"📊 Изменено транслитом: {len(translit_changes)}")
        print(f"📊 Разделено бренд/модель: {len(model_changes)}")
        print(f"📊 Удалено мусора: {len(garbage_deleted)}")
        print(f"📊 Разделено комбинированных: {len(combined_split)}")
        
        remaining = session.exec(select(Brand)).all()
        print(f"\n📊 Осталось брендов: {len(remaining)}")
        print("=" * 70)
