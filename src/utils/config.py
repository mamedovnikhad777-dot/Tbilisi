"""
Настройка конфигурации и логирования
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


def setup_logging():
    """Настройка системы логирования"""
    log_dir = os.getenv('LOG_DIR', 'logs')
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"food_delivery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Преобразуем строку уровня логирования в константу
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Логирование настроено. Уровень: {log_level}")
    return logger


def get_db_config():
    """Получение конфигурации БД из переменных окружения"""
    db_type = os.getenv('DB_TYPE', 'mysql').lower()
    
    if db_type == 'mysql':
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '3306')
        database = os.getenv('DB_NAME')
        username = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        
        if not password:
            raise ValueError("Пароль БД не указан в переменных окружения DB_PASSWORD")
        
        config = {
            'type': 'mysql',
            'url': f'mysql://{username}:{password}@{host}:{port}/{database}',
            'host': host,
            'port': port,
            'database': database,
            'username': username,
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true'
        }
        
    elif db_type == 'sqlite':
        database = os.getenv('DB_NAME', 'food_delivery.db')
        config = {
            'type': 'sqlite',
            'url': f'sqlite://{database}',
            'database': database,
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true'
        }
        
    else:
        raise ValueError(f"Неизвестный тип БД: {db_type}. Поддерживаются: mysql, sqlite")
    
    return config


def print_db_config(config):
    """Вывод информации о конфигурации БД"""
    print("\n" + "="*50)
    print("КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ")
    print("="*50)
    print(f"Тип БД: {config.get('type', 'unknown')}")
    
    if config['type'] == 'mysql':
        print(f"Хост: {config.get('host', 'N/A')}")
        print(f"Порт: {config.get('port', 'N/A')}")
        print(f"База данных: {config.get('database', 'N/A')}")
        print(f"Пользователь: {config.get('username', 'N/A')}")
    elif config['type'] == 'sqlite':
        print(f"Файл БД: {config.get('database', 'N/A')}")
    
    print(f"Режим отладки (echo): {config.get('echo', False)}")
    print("="*50)


def check_env_file():
    """Проверка наличия .env файла"""
    if not os.path.exists('.env'):
        print("⚠️  Файл .env не найден!")
        print("Создайте файл .env из шаблона .env.example")
        print("Команда: cp .env.example .env")
        print("Затем отредактируйте .env файл с вашими настройками")
        return False
    return True
