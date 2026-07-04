"""
Планировщик задач (APScheduler)
Проверяет NotificationTask и отправляет уведомления
"""
import asyncio
from datetime import datetime
from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.database import engine
from models.notification_task import NotificationTask
from models.order import Order
from models.user import User
from core.logging import logger
from services.sms_service import sms_service

# Глобальный экземпляр планировщика
scheduler = AsyncIOScheduler()


async def check_pending_notifications():
    """Проверить и отправить_pending уведомления"""
    now = datetime.now()
    
    with Session(engine) as session:
        # Найти все неотправленные уведомления, время которых пришло
        pending = session.exec(
            select(NotificationTask).where(
                NotificationTask.is_sent == False,
                NotificationTask.send_at <= now,
            )
        ).all()
        
        for task in pending:
            try:
                # Получить заказ
                order = session.get(Order, task.order_id)
                if not order:
                    logger.warning(f"Заказ #{task.order_id} не найден для уведомления #{task.id}")
                    task.is_sent = True  # Пометить как отправленное (заказ удалён)
                    session.add(task)
                    session.commit()
                    continue
                
                # Отправка через Telegram бот
                if task.chat_id:
                    try:
                        from bot.bot import bot as telegram_bot
                        await telegram_bot.send_message(
                            chat_id=task.chat_id,
                            text=task.message_text,
                        )
                        logger.info(f"Telegram уведомление отправлено: task #{task.id}, chat_id={task.chat_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки Telegram: {e}")
                        # Бот заблокирован или ошибка — всё равно помечаем
                        task.is_sent = True
                        session.add(task)
                        session.commit()
                        continue
                
                # Отправка через SMS (если нет chat_id)
                elif task.client_phone:
                    sms_service.send(task.client_phone, task.message_text)
                    logger.info(f"SMS уведомление отправлено: task #{task.id}, phone={task.client_phone}")
                
                # Пометить как отправленное
                task.is_sent = True
                session.add(task)
                session.commit()
                
            except Exception as e:
                logger.error(f"Ошибка обработки уведомления #{task.id}: {e}")
                # Не помечаем is_sent — попробуем в следующий раз


async def send_review_reminder():
    """Отправить напоминание об оценке через 24ч после выдачи"""
    now = datetime.now()
    yesterday = now - timedelta(hours=24)
    
    with Session(engine) as session:
        # Найти заказы, выданные ~24 часа назад
        orders = session.exec(
            select(Order).where(
                Order.status == "issued",
                Order.issued_at >= yesterday - timedelta(hours=1),
                Order.issued_at <= yesterday + timedelta(hours=1),
            )
        ).all()
        
        for order in orders:
            # Найти клиента в боте
            # Если клиент авторизован — отправить ему
            # Пока — заглушка
            logger.info(f"Напоминание об оценке: заказ #{order.id}. Клиент: {order.client_phone}")
            
            # Получить ссылку на отзыв из настроек компании
            from models.company_settings import CompanySettings
            company = session.exec(select(CompanySettings)).first()
            
            if company and company.review_link:
                message = (
                    f"Спасибо что выбрали наш сервисный центр! 🙏\n\n"
                    f"Оцените нашу, пожалуйста:\n{company.review_link}"
                )
                
                # TODO: Отправка через бот или SMS
                logger.info(f"Отзыв: {message}")


def start_scheduler():
    """Запустить планировщик"""
    # Проверка уведомлений каждую минуту
    scheduler.add_job(
        check_pending_notifications,
        "interval",
        minutes=1,
        id="check_notifications",
        replace_existing=True,
    )
    
    # Напоминания об оценке — каждый час
    scheduler.add_job(
        send_review_reminder,
        "interval",
        hours=1,
        id="review_reminders",
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("Планировщик запущен (уведомления: каждую минуту, отзывы: каждый час)")


def stop_scheduler():
    """Остановить планировщик"""
    scheduler.shutdown()
    logger.info("Планировщик остановлен")


# Импорт timedelta
from datetime import timedelta
