"""
Синхронный менеджер базы данных
"""

import logging
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

# Добавляем путь для импорта
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

logger = logging.getLogger(__name__)


class SyncDatabaseManager:
    """Синхронный класс для управления операциями с базой данных"""
    
    _connection = None
    _engine = None
    
    @classmethod
    def init_db(cls, db_config: Dict[str, Any]):
        """Инициализация базы данных"""
        try:
            from sqlalchemy import create_engine, text
            
            if db_config['type'] == 'mysql':
                # Формируем строку подключения для MySQL
                connection_string = f"mysql+pymysql://{db_config.get('username', 'root')}:{db_config.get('password', '0907')}@{db_config.get('host', 'localhost')}:{db_config.get('port', 3306)}/{db_config.get('database', '')}"
            else:
                # SQLite
                connection_string = f"sqlite:///{db_config.get('database', 'phpmyadmin.db')}"
            
            cls._engine = create_engine(connection_string, echo=db_config.get('echo', False))
            cls._connection = cls._engine.connect()
            
            logger.info(f"Успешное подключение к БД: {db_config.get('host', 'localhost')}/{db_config.get('database', '')}")
            
            # Создаем таблицы, если их нет
            cls.create_tables()
            
            # Создаем стандартные статусы
            cls.create_default_statuses()
            
            # Создаем тестовые данные
            cls.create_sample_data()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    @classmethod
    def create_tables(cls):
        """Создание таблиц, если их нет"""
        try:
            from sqlalchemy import text
            
            # Проверяем существование таблицы Statuses
            check_table_sql = """
                CREATE TABLE IF NOT EXISTS Statuses (
                    status_id INT PRIMARY KEY,
                    status_name VARCHAR(50) UNIQUE
                )
            """
            
            cls._connection.execute(text(check_table_sql))
            
            # Таблица Customers
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Customers (
                    customer_id INT AUTO_INCREMENT PRIMARY KEY,
                    phone_number VARCHAR(20) UNIQUE,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100)
                )
            """))
            
            # Таблица Restaurants
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Restaurants (
                    restaurant_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    location VARCHAR(500),
                    rating DECIMAL(3,2)
                )
            """))
            
            # Таблица Dishes
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Dishes (
                    dish_id INT AUTO_INCREMENT PRIMARY KEY,
                    restaurant_id INT,
                    name VARCHAR(255),
                    description TEXT,
                    cooking_time VARCHAR(20),
                    FOREIGN KEY (restaurant_id) REFERENCES Restaurants(restaurant_id)
                )
            """))
            
            # Таблица Couriers
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Couriers (
                    courier_id INT AUTO_INCREMENT PRIMARY KEY,
                    phone_number VARCHAR(20) UNIQUE,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    car_number VARCHAR(20) UNIQUE
                )
            """))
            
            # Таблица Orders
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Orders (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT,
                    status_id INT,
                    order_time DATETIME,
                    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
                    FOREIGN KEY (status_id) REFERENCES Statuses(status_id)
                )
            """))
            
            # Таблица OrderItems
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS OrderItems (
                    order_id INT,
                    dish_id INT,
                    quantity INT DEFAULT 1,
                    PRIMARY KEY (order_id, dish_id),
                    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
                    FOREIGN KEY (dish_id) REFERENCES Dishes(dish_id)
                )
            """))
            
            # Таблица Deliveries
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Deliveries (
                    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT,
                    courier_id INT,
                    delivery_time DATETIME,
                    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
                    FOREIGN KEY (courier_id) REFERENCES Couriers(courier_id)
                )
            """))
            
            # Таблица Reviews
            cls._connection.execute(text("""
                CREATE TABLE IF NOT EXISTS Reviews (
                    review_id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT,
                    rating INT,
                    description TEXT,
                    FOREIGN KEY (order_id) REFERENCES Orders(order_id)
                )
            """))
            
            logger.info("Таблицы созданы или уже существуют")
            
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {str(e)}")
            raise
    
    @classmethod
    def create_default_statuses(cls):
        """Создание стандартных статусов заказов"""
        try:
            from sqlalchemy import text
            
            statuses = [
                (1, 'Принят'),
                (2, 'Готовится'),
                (3, 'Готов'),
                (4, 'В доставке'),
                (5, 'Доставлен'),
                (6, 'Отменен')
            ]
            
            for status_id, status_name in statuses:
                # Проверяем, существует ли уже статус
                check_sql = "SELECT COUNT(*) FROM Statuses WHERE status_id = :status_id"
                result = cls._connection.execute(text(check_sql), {"status_id": status_id}).scalar()
                
                if result == 0:
                    insert_sql = "INSERT INTO Statuses (status_id, status_name) VALUES (:status_id, :status_name)"
                    cls._connection.execute(text(insert_sql), {"status_id": status_id, "status_name": status_name})
                    logger.info(f"Создан статус: {status_name}")
            
            cls._connection.commit()
            
        except Exception as e:
            logger.error(f"Ошибка создания стандартных статусов: {str(e)}")
    
    @classmethod
    def create_sample_data(cls):
        """Создание тестовых данных"""
        try:
            from sqlalchemy import text
            
            # Проверяем и создаем ресторан "Тбилиси"
            check_restaurant_sql = "SELECT restaurant_id FROM Restaurants WHERE name = 'Тбилиси' LIMIT 1"
            result = cls._connection.execute(text(check_restaurant_sql))
            restaurant = result.fetchone()
            
            if not restaurant:
                # Создаем ресторан
                insert_restaurant_sql = """
                    INSERT INTO Restaurants (name, location, rating) 
                    VALUES ('Тбилиси', 'ул. Грузинская, 15', 4.7)
                """
                cls._connection.execute(text(insert_restaurant_sql))
                restaurant_id = cls._connection.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                logger.info(f"Создан ресторан 'Тбилиси' (ID: {restaurant_id})")
            else:
                restaurant_id = restaurant[0]
                logger.info(f"Ресторан 'Тбилиси' уже существует (ID: {restaurant_id})")
            
            # Проверяем и создаем блюда
            check_dishes_sql = "SELECT COUNT(*) FROM Dishes WHERE restaurant_id = :restaurant_id"
            dishes_count = cls._connection.execute(
                text(check_dishes_sql), 
                {"restaurant_id": restaurant_id}
            ).scalar()
            
            if dishes_count == 0:
                dishes_data = [
                    ('Хачапури по-аджарски', 'Традиционное грузинское блюдо с сыром сулугуни и яйцом', '25'),
                    ('Хинкали', 'Грузинские пельмени с сочной мясной начинкой', '30'),
                    ('Сациви', 'Курица в ореховом соусе с травами', '40'),
                    ('Лобио', 'Грузинское блюдо из красной фасоли с грецкими орехами', '35'),
                    ('Шашлык из свинины', 'Нежное мясо на мангале с луком и гранатом', '20'),
                    ('Чашушули', 'Острое мясное рагу с томатами и перцем', '45'),
                    ('Пхали', 'Закуска из шпината с орехами и специями', '15'),
                    ('Чихохбили', 'Грузинское тушеное мясо с томатами', '50'),
                    ('Купаты', 'Грузинские колбаски на гриле', '25'),
                    ('Эларджи', 'Каша из кукурузной муки с сыром сулугуни', '30')
                ]
                
                for dish_name, description, cooking_time in dishes_data:
                    insert_dish_sql = """
                        INSERT INTO Dishes (restaurant_id, name, description, cooking_time)
                        VALUES (:restaurant_id, :name, :description, :cooking_time)
                    """
                    cls._connection.execute(text(insert_dish_sql), {
                        "restaurant_id": restaurant_id,
                        "name": dish_name,
                        "description": description,
                        "cooking_time": cooking_time
                    })
                
                logger.info(f"Созданы 10 блюд для ресторана 'Тбилиси'")
            else:
                logger.info(f"Блюда для ресторана 'Тбилиси' уже существуют ({dishes_count} шт.)")
            
            # Проверяем и создаем тестовых клиентов
            customers_count = cls._connection.execute(text("SELECT COUNT(*) FROM Customers")).scalar()
            if customers_count == 0:
                customers_data = [
                    ('+79161234567', 'Иван', 'Петров'),
                    ('+79262345678', 'Мария', 'Сидорова'),
                    ('+79363456789', 'Алексей', 'Козlov')
                ]
                
                for phone_number, first_name, last_name in customers_data:
                    insert_customer_sql = """
                        INSERT INTO Customers (phone_number, first_name, last_name)
                        VALUES (:phone_number, :first_name, :last_name)
                    """
                    cls._connection.execute(text(insert_customer_sql), {
                        "phone_number": phone_number,
                        "first_name": first_name,
                        "last_name": last_name
                    })
                
                logger.info("Созданы тестовые клиенты")
            else:
                logger.info(f"Клиенты уже существуют ({customers_count} шт.)")
            
            # Проверяем и создаем тестовых курьеров
            couriers_count = cls._connection.execute(text("SELECT COUNT(*) FROM Couriers")).scalar()
            if couriers_count == 0:
                couriers_data = [
                    ('+79464567890', 'Дмитрий', 'Иванов', 'A123BC'),
                    ('+79565678901', 'Ольга', 'Николаева', 'B456DE')
                ]
                
                for phone_number, first_name, last_name, car_number in couriers_data:
                    insert_courier_sql = """
                        INSERT INTO Couriers (phone_number, first_name, last_name, car_number)
                        VALUES (:phone_number, :first_name, :last_name, :car_number)
                    """
                    cls._connection.execute(text(insert_courier_sql), {
                        "phone_number": phone_number,
                        "first_name": first_name,
                        "last_name": last_name,
                        "car_number": car_number
                    })
                
                logger.info("Созданы тестовые курьеры")
            else:
                logger.info(f"Курьеры уже существуют ({couriers_count} шт.)")
            
            cls._connection.commit()
            
        except Exception as e:
            logger.error(f"Ошибка создания тестовых данных: {str(e)}")
            cls._connection.rollback()
            raise
    
    @classmethod
    def get_all(cls, table_name: str) -> List[Dict[str, Any]]:
        """Получение всех записей из таблицы"""
        try:
            from sqlalchemy import text
            
            query = f"SELECT * FROM {table_name}"
            result = cls._connection.execute(text(query))
            
            # Преобразуем результат в список словарей
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            logger.debug(f"Получено {len(rows)} записей из {table_name}")
            return rows
            
        except Exception as e:
            logger.error(f"Ошибка получения данных из {table_name}: {str(e)}")
            raise
    
    @classmethod
    def get_customers(cls) -> List[Dict[str, Any]]:
        """Получение всех клиентов"""
        return cls.get_all("Customers")
    
    @classmethod
    def get_restaurants(cls) -> List[Dict[str, Any]]:
        """Получение всех ресторанов"""
        return cls.get_all("Restaurants")
    
    @classmethod
    def get_dishes(cls) -> List[Dict[str, Any]]:
        """Получение всех блюд"""
        return cls.get_all("Dishes")
    
    @classmethod
    def get_couriers(cls) -> List[Dict[str, Any]]:
        """Получение всех курьеров"""
        return cls.get_all("Couriers")
    
    @classmethod
    def get_orders(cls) -> List[Dict[str, Any]]:
        """Получение всех заказов"""
        return cls.get_all("Orders")
    
    @classmethod
    def get_orders_with_details(cls) -> List[Dict[str, Any]]:
        """Получение заказов с деталями"""
        try:
            from sqlalchemy import text
            
            query = """
                SELECT o.order_id, 
                    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
                    s.status_name,
                    o.order_time,
                    COUNT(oi.order_id) as items_count,
                    COALESCE(SUM(oi.quantity), 0) as total_quantity
                FROM Orders o
                LEFT JOIN Customers c ON o.customer_id = c.customer_id
                LEFT JOIN Statuses s ON o.status_id = s.status_id
                LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
                GROUP BY o.order_id, c.first_name, c.last_name, s.status_name, o.order_time
                ORDER BY o.order_time DESC
            """
            
            result = cls._connection.execute(text(query))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return rows
            
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказов: {str(e)}")
            return []
    
    @classmethod
    def get_dishes_by_restaurant(cls, restaurant_id: int) -> List[Dict[str, Any]]:
        """Получение блюд по ресторану"""
        try:
            from sqlalchemy import text
            
            query = "SELECT * FROM Dishes WHERE restaurant_id = :restaurant_id"
            result = cls._connection.execute(text(query), {"restaurant_id": restaurant_id})
            
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            return rows
            
        except Exception as e:
            logger.error(f"Ошибка получения блюд ресторана: {str(e)}")
            return []
    
    @classmethod
    def create_order(cls, customer_id: int, dish_quantities: List[Tuple[int, int]], courier_id: Optional[int] = None) -> int:
        """Создание нового заказа"""
        try:
            from sqlalchemy import text
            
            # Начинаем транзакцию
            trans = cls._connection.begin()
            
            try:
                # Создаем заказ
                insert_order_sql = """
                    INSERT INTO Orders (customer_id, status_id, order_time)
                    VALUES (:customer_id, 1, :order_time)
                """
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cls._connection.execute(
                    text(insert_order_sql), 
                    {"customer_id": customer_id, "order_time": current_time}
                )
                
                # Получаем ID созданного заказа
                order_id = cls._connection.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                
                # Добавляем позиции заказа
                for dish_id, quantity in dish_quantities:
                    insert_item_sql = """
                        INSERT INTO OrderItems (order_id, dish_id, quantity)
                        VALUES (:order_id, :dish_id, :quantity)
                    """
                    cls._connection.execute(
                        text(insert_item_sql), 
                        {"order_id": order_id, "dish_id": dish_id, "quantity": quantity}
                    )
                
                # Создаем доставку
                if courier_id:
                    insert_delivery_sql = """
                        INSERT INTO Deliveries (order_id, courier_id, delivery_time)
                        VALUES (:order_id, :courier_id, NULL)
                    """
                    cls._connection.execute(
                        text(insert_delivery_sql), 
                        {"order_id": order_id, "courier_id": courier_id}
                    )
                else:
                    # Назначаем первого курьера, если не указан
                    couriers = cls.get_couriers()
                    if couriers:
                        insert_delivery_sql = """
                            INSERT INTO Deliveries (order_id, courier_id, delivery_time)
                            VALUES (:order_id, :courier_id, NULL)
                        """
                        cls._connection.execute(
                            text(insert_delivery_sql), 
                            {"order_id": order_id, "courier_id": couriers[0]['courier_id']}
                        )
                
                # Фиксируем транзакцию
                trans.commit()
                
                logger.info(f"Создан заказ #{order_id} с {len(dish_quantities)} позициями")
                return order_id
                
            except Exception as e:
                trans.rollback()
                raise
                
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {str(e)}")
            raise
    
    @classmethod
    def close(cls):
        """Закрытие соединения с базой данных"""
        try:
            if cls._connection:
                cls._connection.close()
            if cls._engine:
                cls._engine.dispose()
            logger.info("Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии соединения: {str(e)}")
