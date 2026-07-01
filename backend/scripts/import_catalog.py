"""
Скрипт импорта категорий и брендов из CSV файла
Использование:
    cd backend
    source venv/bin/activate
    python scripts/import_catalog.py ../cat.csv
"""

import sys
import csv
from pathlib import Path

# Добавляем корень backend в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.category import Category
from models.brand import Brand


def normalize_name(name: str) -> str:
    """Нормализация названия: убираем пробелы, приводим к правильному регистру"""
    if not name:
        return ""
    # Убираем лишние пробелы
    name = name.strip()
    # Если все заглавные - делаем Title Case
    if name.isupper():
        name = name.title()
    return name


def import_catalog(csv_path: str):
    """Импорт категорий и брендов из CSV"""
    
    print(f"📂 Импорт из файла: {csv_path}")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # Считываем CSV с обработкой BOM
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            categories_added = set()
            brands_added = set()
            categories_count = 0
            brands_count = 0
            
            for row in reader:
                # Категория (Вид устройства)
                category_name = normalize_name(row.get('Вид устройства', ''))
                if category_name and category_name not in categories_added:
                    # Проверяем существует ли уже
                    existing = session.exec(
                        select(Category).where(Category.name.ilike(category_name))
                    ).first()
                    
                    if not existing:
                        cat = Category(name=category_name, is_active=True)
                        session.add(cat)
                        categories_added.add(category_name)
                        categories_count += 1
                        print(f"  ➕ Категория: {category_name}")
                
                # Бренд
                brand_name = normalize_name(row.get('Бренд', ''))
                if brand_name and brand_name not in brands_added:
                    # Проверяем существует ли уже
                    existing = session.exec(
                        select(Brand).where(Brand.name.ilike(brand_name))
                    ).first()
                    
                    if not existing:
                        brand = Brand(name=brand_name, is_active=True)
                        session.add(brand)
                        brands_added.add(brand_name)
                        brands_count += 1
                        print(f"  ➕ Бренд: {brand_name}")
            
            # Сохраняем всё сразу
            session.commit()
            
            print(f"\n✅ Импорт завершён!")
            print(f"   Добавлено категорий: {categories_count}")
            print(f"   Добавлено брендов: {brands_count}")
            print(f"\n📊 Всего в базе:")
            
            total_categories = session.exec(select(Category)).all()
            total_brands = session.exec(select(Brand)).all()
            
            print(f"   Категорий: {len(total_categories)}")
            print(f"   Брендов: {len(total_brands)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Укажите путь к CSV файлу")
        print("Пример: python scripts/import_catalog.py ../cat.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"❌ Файл не найден: {csv_file}")
        sys.exit(1)
    
    import_catalog(csv_file)
