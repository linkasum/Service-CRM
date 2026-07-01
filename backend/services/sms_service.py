"""
SMS сервис (заглушка)
Место для интеграции с SMS-провайдером (SMS.ru, Twilio и т.д.)
"""
from typing import Optional
from core.config import get_settings
from core.logging import logger

settings = get_settings()


class SMSService:
    """
    Сервис отправки SMS.
    
    Сейчас — заглушка (логирование в консоль).
    Для подключения реального провайдера:
    1. Установить SDK (например, smsru или twilio)
    2. Добавить SMS_API_KEY в .env
    3. Реализовать метод send()
    """
    
    def __init__(self):
        self.api_key = settings.SMS_API_KEY
        self.enabled = settings.SMS_SERVICE_ENABLED
    
    def send(self, phone: str, message: str) -> bool:
        """
        Отправить SMS.
        
        Args:
            phone: Номер телефона (например, +79991234567)
            message: Текст сообщения
        
        Returns:
            True если отправлено, False если заглушка или ошибка
        """
        if not self.enabled:
            # Заглушка — логирование
            logger.info(f"[SMS ЗАГЛУШКА] {phone}: {message}")
            return True
        
        # TODO: Реальная отправка SMS
        # Пример для SMS.ru:
        # import smsru
        # client = smsru.SmsRu(self.api_key)
        # result = client.send_sms(phone, message)
        # return result.code == '100'
        
        logger.warning(f"SMS сервис включён, но не настроен. Сообщение для {phone}: {message}")
        return False
    
    def send_order_ready(self, phone: str, order_id: int, device: str) -> bool:
        """Отправить SMS о готовности заказа"""
        message = f"Ваш заказ #{order_id} ({device}) готов к выдаче!"
        return self.send(phone, message)
    
    def send_order_status(self, phone: str, order_id: int, status: str) -> bool:
        """Отправить SMS о смене статуса заказа"""
        status_messages = {
            "diagnostics": f"Заказ #{order_id} принят в диагностику.",
            "agreed": f"Заказ #{order_id}: стоимость согласована.",
            "repair": f"Заказ #{order_id} передан в ремонт.",
            "ready": f"Заказ #{order_id} готов к выдаче!",
        }
        message = status_messages.get(status, f"Статус заказа #{order_id} изменён на {status}.")
        return self.send(phone, message)


# Синглтон
sms_service = SMSService()
