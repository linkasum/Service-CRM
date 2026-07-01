"""
Главное приложение FastAPI
"""
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlalchemy.exc import SQLAlchemyError

from core.logging import logger
from core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """События запуска и остановки приложения"""
    # При запуске
    logger.info("Запуск CRM-системы...")
    create_db_and_tables()
    logger.info("База данных инициализирована")
    
    # Запуск планировщика
    from services.scheduler import start_scheduler
    start_scheduler()
    logger.info("Планировщик уведомлений запущен")
    
    # Запуск Telegram бота в фоне (отдельный процесс — run_bot.py)
    # Бот запускается командой: cd backend && python run_bot.py
    # Здесь только логирование
    from core.config import get_settings
    _settings = get_settings()
    if _settings.TELEGRAM_BOT_TOKEN:
        logger.info("Telegram бот: запустите 'cd backend && python run_bot.py'")
    else:
        logger.info("Telegram бот: TELEGRAM_BOT_TOKEN не настроен")

    yield

    # При остановке
    from services.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("Остановка CRM-системы")


app = FastAPI(
    title="CRM Система для сервисного центра",
    description="Управление ремонтами, складом, зарплатами и клиентами",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:80", "http://127.0.0.1:5173", "http://127.0.0.1:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключение маршрутов
from routes.auth import router as auth_router
from routes.orders import router as orders_router
from routes.parts import router as parts_router
from routes.clients import router as clients_router
from routes.reports import router as reports_router
from routes.salary import router as salary_router
from routes.settings import router as settings_router
from routes.settings_extra import router as settings_extra_router
from routes.documents import router as documents_router
from routes.users import router as users_router
from routes.permissions import router as permissions_router
from routes.bot_management import router as bot_router
from routes.order_comments import router as comments_router
from routes.templates import router as templates_router
from routes.payments import router as payments_router
from routes.services import router as services_router
from routes.order_parts import router as order_parts_router
from routes.order_services import router as order_services_router
from routes.orders_services import router as orders_services_router
from routes.orders_parts import router as orders_parts_router
from routes.search import router as search_router
from routes.export import router as export_router
from routes.cash import router as cash_router
from routes.salary_assignment import router as salary_assignment_router
from routes.database import router as database_router
from routes.device_models import router as device_models_router
from routes.working_hours import router as working_hours_router
from routes.notifications import router as notifications_router
from routes.work_schedule import router as work_schedule_router

app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(parts_router)
app.include_router(clients_router)
app.include_router(reports_router)
app.include_router(salary_router)
app.include_router(settings_router)
app.include_router(settings_extra_router)
app.include_router(documents_router)
app.include_router(users_router)
app.include_router(permissions_router)
app.include_router(bot_router)
app.include_router(comments_router)
app.include_router(templates_router)
app.include_router(payments_router)
app.include_router(services_router)
app.include_router(order_parts_router)
app.include_router(notifications_router)
app.include_router(order_services_router)
app.include_router(orders_services_router)
app.include_router(orders_parts_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(cash_router)
app.include_router(salary_assignment_router)
app.include_router(database_router)
app.include_router(device_models_router)
app.include_router(working_hours_router)
app.include_router(work_schedule_router)

# WebSocket endpoint (нельзя включать через include_router)
from routes.websocket import websocket_endpoint
app.add_api_websocket_route("/ws", websocket_endpoint)


# === Глобальные обработчики ошибок ===

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработка ошибок валидации"""
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })
    logger.warning(f"Ошибка валидации: {errors}")
    return JSONResponse(
        status_code=422,
        content={"detail": "Ошибка валидации", "errors": errors},
    )


@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Обработка ошибок базы данных"""
    logger.error(f"Ошибка БД: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера (база данных)"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Обработка всех остальных ошибок"""
    logger.error(f"Необработанная ошибка: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )


@app.get("/api/health", tags=["Системное"])
def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
