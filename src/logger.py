"""
Система логирования для игры Auto Arsenal.
Записывает логи в файл и консоль с разными уровнями важности.
"""

import logging
import os
from datetime import datetime


class GameLogger:
    """Централизованная система логирования игры."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        
        # Создаём папку для логов
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Имя файла с датой и временем
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"game_{timestamp}.log")
        
        # Настройка основного логгера
        self.logger = logging.getLogger("AutoArsenal")
        self.logger.setLevel(logging.DEBUG)
        
        # Формат логов
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Обработчик для файла (все уровни)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Обработчик для консоли (только INFO и выше)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.logger.info("=" * 60)
        self.logger.info("Система логирования Auto Arsenal инициализирована")
        self.logger.info(f"Файл логов: {log_file}")
        self.logger.info("=" * 60)
    
    def debug(self, message):
        """Отладочная информация (детали работы)"""
        self.logger.debug(message)
    
    def info(self, message):
        """Информационное сообщение (важные события)"""
        self.logger.info(message)
    
    def warning(self, message):
        """Предупреждение (потенциальная проблема)"""
        self.logger.warning(message)
    
    def error(self, message):
        """Ошибка (что-то пошло не так)"""
        self.logger.error(message)
    
    def critical(self, message):
        """Критическая ошибка (игра может упасть)"""
        self.logger.critical(message)
    
    def game_event(self, event_type, **kwargs):
        """Логирование игровых событий с дополнительными данными"""
        details = ", ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"[GAME_EVENT] {event_type}: {details}")
    
    def performance(self, metric_name, value):
        """Логирование метрик производительности"""
        self.logger.debug(f"[PERFORMANCE] {metric_name}: {value}")


# Глобальный экземпляр логгера
_logger = None

def get_logger():
    """Получить глобальный экземпляр логгера"""
    global _logger
    if _logger is None:
        _logger = GameLogger()
    return _logger
