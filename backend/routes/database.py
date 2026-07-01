"""
API для просмотра базы данных (только для админов)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text, inspect
from sqlmodel import Session, select
from core.database import get_session
from core.security import get_current_user
from models.user import User
from models.role import Role

router = APIRouter(prefix="/api/database", tags=["Database"])


def require_admin(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Требует права администратора"""
    # Загружаем роль явно
    if current_user.role_id:
        role = session.get(Role, current_user.role_id)
        if role and role.name == "admin":
            return current_user
    raise HTTPException(status_code=403, detail="Доступно только администраторам")


@router.get("/tables")
def get_tables(current_user: User = Depends(require_admin), session: Session = Depends(get_session)):
    """Получить список всех таблиц"""
    conn = session.bind
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    result = []
    for table in tables:
        columns = inspector.get_columns(table)
        result.append({
            "name": table,
            "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns]
        })
    
    return result


@router.get("/table/{table_name}")
def get_table_data(
    table_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """Получить данные таблицы с пагинацией"""
    conn = session.bind
    
    # Проверка существования таблицы
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Таблица '{table_name}' не найдена")
    
    # Получаем колонки
    columns = inspector.get_columns(table_name)
    column_names = [col["name"] for col in columns]
    
    # Экранируем имя таблицы
    safe_table_name = f'"{table_name}"'
    
    # Считаем общее количество
    count_query = text(f"SELECT COUNT(*) FROM {safe_table_name}")
    total = session.execute(count_query).scalar()
    
    # Получаем данные с пагинацией
    offset = (page - 1) * page_size
    data_query = text(f"SELECT * FROM {safe_table_name} ORDER BY 1 DESC LIMIT :limit OFFSET :offset")
    result = session.execute(data_query, {"limit": page_size, "offset": offset})
    
    rows = []
    for row in result:
        rows.append(dict(zip(column_names, row)))
    
    return {
        "table": table_name,
        "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
        "data": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.post("/query")
def execute_query(
    query: str,
    current_user: User = Depends(require_admin),
    session: Session = Depends(get_session)
):
    """
    Выполнить SQL запрос (только SELECT)
    
    ⚠️ Разрешены только SELECT запросы
    """
    # Проверка на SELECT
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise HTTPException(status_code=403, detail="Разрешены только SELECT запросы")
    
    # Блокировка опасных операций
    dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise HTTPException(status_code=403, detail=f"Запрос содержит запрещённую операцию: {keyword}")
    
    try:
        result = session.execute(text(query))
        rows = [dict(row._mapping) for row in result]
        
        # Получаем описание колонок
        if result.keys():
            columns = [{"name": key, "type": "unknown"} for key in result.keys()]
        else:
            columns = []
        
        return {
            "columns": columns,
            "data": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка выполнения запроса: {str(e)}")
