"""
Настройка логирования
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(log_level: str = "INFO"):
    """Настроить логирование в файлы и консоль"""
    
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Основной лог
    main_logger = logging.getLogger("qwencrm")
    main_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Файл ошибок
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "error.log"),
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Файл доступа
    access_handler = RotatingFileHandler(
        os.path.join(log_dir, "access.log"),
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(formatter)
    
    # Консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    
    main_logger.addHandler(error_handler)
    main_logger.addHandler(access_handler)
    main_logger.addHandler(console_handler)
    
    return main_logger


logger = setup_logging()
