"""
Чистка мусорных записей в справочниках
Удаляет категории и бренды состоящие из символов
Использование:
    cd backend
    source venv/bin/activate
    python scripts/cleanup_garbage.py
"""

import sys
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, select
from core.database import engine
from models.category import Category
from models.brand import Brand


def is_garbage(name: str) -> bool:
    """Проверяет является ли название мусором"""
    if not name or len(name.strip()) == 0:
        return True
    
    # Только спецсимволы
    if re.match(r'^[\s\-\*=\.\/\\,;:!?]+$|^-$|^\*+$', name.strip()):
        return True
    
    # Слишком короткое (1-2 символа без букв)
    letters = sum(1 for c in name if c.isalpha())
    if letters < 2 and len(name) <= 3:
        return True
    
    return False


def cleanup_garbage():
    """Чистка мусора"""
    print("\n🧹 Чистка мусорных записей...")
    
    with engine.connect() as conn:
        session = Session(conn)
        
        # Категории
        all_cats = session.exec(select(Category)).all()
        cat_deleted = 0
        
        for cat in all_cats:
            if is_garbage(cat.name):
                print(f"   ❌ Категория: '{cat.name}'")
                session.delete(cat)
                cat_deleted += 1
        
        # Бренды
        all_brands = session.exec(select(Brand)).all()
        brand_deleted = 0
        
        for brand in all_brands:
            if is_garbage(brand.name):
                print(f"   ❌ Бренд: '{brand.name}'")
                session.delete(brand)
                brand_deleted += 1
        
        session.commit()
        
        print(f"\n✅ Удалено мусора:")
        print(f"   Категорий: {cat_deleted}")
        print(f"   Брендов: {brand_deleted}")
        
        # Финальная статистика
        remaining_cats = session.exec(select(Category)).all()
        remaining_brands = session.exec(select(Brand)).all()
        
        print(f"\n📊 Осталось:")
        print(f"   Категорий: {len(remaining_cats)}")
        print(f"   Брендов: {len(remaining_brands)}")


if __name__ == "__main__":
    print("=" * 70)
    print("🧹 Чистка мусорных записей")
    print("=" * 70)
    
    cleanup_garbage()
    
    print("\n" + "=" * 70)
    print("✅ Чистка завершена!")
    print("=" * 70)
