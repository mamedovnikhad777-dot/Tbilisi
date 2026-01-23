"""
Модуль для инициализации базы данных
"""

import logging
import asyncio
from tortoise import Tortoise
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Класс для инициализации базы данных"""
    
    _initialized = False
    _lock = asyncio.Lock()
    
    @classmethod
    async def initialize(cls):
        """Асинхронная инициализация базы данных"""
        async with cls._lock:
            if cls._initialized:
                return
            
            try:
                logger.info("Начало инициализации базы данных")
                
                # Инициализируем Tortoise
                await DatabaseManager.init_db()
                
                cls._initialized = True
                logger.info("База данных успешно инициализирована")
                
            except Exception as e:
                logger.error(f"Ошибка инициализации базы данных: {str(e)}")
                raise
    
    @classmethod
    async def get_connection(cls):
        """Получение соединения с базой данных"""
        if not cls._initialized:
            await cls.initialize()
        
        from tortoise import connections
        return connections.get('default')
    
    @classmethod
    def run_sync_initialization(cls):
        """Синхронная инициализация базы данных"""
        try:
            # Создаем новый event loop для инициализации
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем инициализацию
            loop.run_until_complete(cls.initialize())
            
            # Закрываем loop
            loop.close()
            
            return True
        except Exception as e:
            logger.error(f"Синхронная инициализация базы данных не удалась: {str(e)}")
            return False
