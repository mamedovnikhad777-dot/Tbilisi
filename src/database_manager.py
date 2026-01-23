"""
Менеджер базы данных
"""

import logging
import traceback
from datetime import datetime
from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from .models import (
    Statuses, Customers, Restaurants, Dishes,
    Couriers, Orders, OrderItems, Deliveries, Reviews
)
from .utils.async_helper import async_helper

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Класс для управления операциями с базой данных"""
    
    db_config = None
    
    @classmethod
    def set_db_config(cls, config):
        """Установка конфигурации БД"""
        cls.db_config = config
        logger.info(f"Установлена конфигурация БД: {config['type']} - {config['host']}/{config['database']}")
    
    @classmethod
    async def init_db(cls):
        """Асинхронная инициализация БД"""
        try:
            if cls.db_config is None:
                await Tortoise.init(
                    db_url='sqlite://phpmyadmin.db',
                    modules={'models': ['src.models']}
                )
                logger.info("Инициализирована база данных SQLite по умолчанию")
            else:
                await Tortoise.init(
                    db_url=cls.db_config['url'],
                    modules={'models': ['src.models']}
                )
                logger.info(f"Успешное подключение к БД: {cls.db_config['host']}/{cls.db_config['database']}")
            
            await cls.create_default_statuses()
            await cls.create_sample_data()
            
        except Exception as e:
            logger.error(f"Ошибка инициализации БД: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    @classmethod
    async def check_connection(cls):
        """Проверка подключения к базе данных"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            # Простой запрос для проверки соединения
            await connection.execute_query("SELECT 1")
            logger.info("Подключение к БД успешно проверено")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {str(e)}")
            return False
    
    @classmethod
    async def create_default_statuses(cls):
        """Создание стандартных статусов заказов"""
        try:
            statuses = [
                {'status_id': 1, 'status_name': 'Принят'},
                {'status_id': 2, 'status_name': 'Готовится'},
                {'status_id': 3, 'status_name': 'Готов'},
                {'status_id': 4, 'status_name': 'В доставке'},
                {'status_id': 5, 'status_name': 'Доставлен'},
                {'status_id': 6, 'status_name': 'Отменен'}
            ]
            
            for status_data in statuses:
                existing = await Statuses.filter(status_id=status_data['status_id']).first()
                if not existing:
                    await Statuses.create(**status_data)
                    logger.info(f"Создан статус: {status_data['status_name']}")
                    
        except Exception as e:
            logger.error(f"Ошибка создания стандартных статусов: {str(e)}")

    @classmethod
    async def create_sample_data(cls):
        """Создание тестовых данных БЕЗ удаления существующих"""
        try:
            # Создаем ресторан "Тбилиси", если его нет
            restaurant = await Restaurants.filter(name="Тбилиси").first()
            if not restaurant:
                restaurant = await Restaurants.create(
                    name="Тбилиси",
                    location="ул. Грузинская, 15",
                    rating=4.7
                )
                logger.info("Создан ресторан 'Тбилиси'")
            else:
                logger.info(f"Ресторан 'Тбилиси' уже существует (ID: {restaurant.restaurant_id})")

            # Создаем блюда для ресторана ТОЛЬКО если их нет
            existing_dishes = await Dishes.filter(restaurant_id=restaurant.restaurant_id).all()
            if not existing_dishes:
                dishes_data = [
                    {
                        'name': 'Хачапури по-аджарски',
                        'description': 'Традиционное грузинское блюдо с сыром сулугуни и яйцом',
                        'cooking_time': '25'
                    },
                    {
                        'name': 'Хинкали',
                        'description': 'Грузинские пельмени с сочной мясной начинкой',
                        'cooking_time': '30'
                    },
                    {
                        'name': 'Сациви',
                        'description': 'Курица в ореховом соусе с травами',
                        'cooking_time': '40'
                    },
                    {
                        'name': 'Лобио',
                        'description': 'Грузинское блюдо из красной фасоли с грецкими орехами',
                        'cooking_time': '35'
                    },
                    {
                        'name': 'Шашлык из свинины',
                        'description': 'Нежное мясо на мангале с луком и гранатом',
                        'cooking_time': '20'
                    },
                    {
                        'name': 'Чашушули',
                        'description': 'Острое мясное рагу с томатами и перцем',
                        'cooking_time': '45'
                    },
                    {
                        'name': 'Пхали',
                        'description': 'Закуска из шпината с орехами и специями',
                        'cooking_time': '15'
                    },
                    {
                        'name': 'Чихохбили',
                        'description': 'Грузинское тушеное мясо с томатами',
                        'cooking_time': '50'
                    },
                    {
                        'name': 'Купаты',
                        'description': 'Грузинские колбаски на гриле',
                        'cooking_time': '25'
                    },
                    {
                        'name': 'Эларджи',
                        'description': 'Каша из кукурузной муки с сыром сулугуни',
                        'cooking_time': '30'
                    }
                ]
                
                for dish_data in dishes_data:
                    await Dishes.create(
                        restaurant_id=restaurant.restaurant_id,
                        **dish_data
                    )
                logger.info("Созданы 10 блюд для ресторана 'Тбилиси'")
            else:
                logger.info(f"Блюда для ресторана 'Тбилиси' уже существуют ({len(existing_dishes)} шт.)")

            # Создаем тестовых клиентов только если их нет
            customers_count = await Customers.all().count()
            if customers_count == 0:
                customers_data = [
                    {'phone_number': '+79161234567', 'first_name': 'Иван', 'last_name': 'Петров'},
                    {'phone_number': '+79262345678', 'first_name': 'Мария', 'last_name': 'Сидорова'},
                    {'phone_number': '+79363456789', 'first_name': 'Алексей', 'last_name': 'Козlov'}
                ]
                
                for customer_data in customers_data:
                    await Customers.create(**customer_data)
                logger.info("Созданы тестовые клиенты")
            else:
                logger.info(f"Клиенты уже существуют ({customers_count} шт.)")

            # Создаем тестовых курьеров только если их нет
            couriers_count = await Couriers.all().count()
            if couriers_count == 0:
                couriers_data = [
                    {'phone_number': '+79464567890', 'first_name': 'Дмитрий', 'last_name': 'Иванов', 'car_number': 'A123BC'},
                    {'phone_number': '+79565678901', 'first_name': 'Ольга', 'last_name': 'Николаева', 'car_number': 'B456DE'}
                ]
                
                for courier_data in couriers_data:
                    await Couriers.create(**courier_data)
                logger.info("Созданы тестовые курьеры")
            else:
                logger.info(f"Курьеры уже существуют ({couriers_count} шт.)")
                    
        except Exception as e:
            logger.error(f"Ошибка создания тестовых данных: {str(e)}")

    # =========================================================================
    # ОСНОВНЫЕ CRUD ОПЕРАЦИИ
    # =========================================================================
    @classmethod
    async def get_all(cls, model_class):
        """Получение всех записей модели"""
        try:
            result = await model_class.all()
            logger.debug(f"Получено {len(result)} записей из {model_class.__name__}")
            return result
        except Exception as e:
            logger.error(f"Ошибка получения данных из {model_class.__name__}: {str(e)}")
            raise

    @classmethod
    async def create_record(cls, model_class, **kwargs):
        """Создание новой записи"""
        try:
            result = await model_class.create(**kwargs)
            logger.info(f"Создана запись в {model_class.__name__}: {kwargs}")
            return result
        except Exception as e:
            logger.error(f"Ошибка создания записи в {model_class.__name__}: {str(e)}")
            raise

    @classmethod
    async def update_record(cls, record, **kwargs):
        """Обновление существующей записи"""
        try:
            pk_name = record._meta.pk_attr
            record_id = getattr(record, pk_name)
            
            await record.update_from_dict(kwargs).save()
            logger.info(f"Обновлена запись {record.__class__.__name__} ID {record_id}: {kwargs}")
            return record
        except Exception as e:
            logger.error(f"Ошибка обновления записи {record.__class__.__name__}: {str(e)}")
            raise

    @classmethod
    async def delete_record(cls, record):
        """Удаление записи с обработкой зависимостей"""
        try:
            # Получаем информацию о записи
            pk_name = record._meta.pk_attr
            record_id = getattr(record, pk_name)
            record_class_name = record.__class__.__name__
            
            logger.info(f"Попытка удаления {record_class_name} ID {record_id}")
            
            # Обрабатываем разные типы записей
            if record_class_name == "Orders":
                return await cls.delete_order_cascade(record_id)
            elif record_class_name == "Dishes":
                return await cls.delete_dish_cascade(record_id)
            elif record_class_name == "Restaurants":
                return await cls.delete_restaurant_cascade(record_id)
            elif record_class_name == "Customers":
                # Проверяем, есть ли заказы у клиента
                orders_count = await Orders.filter(customer_id=record_id).count()
                if orders_count > 0:
                    return False, f"Невозможно удалить клиента: у него {orders_count} заказов"
                await record.delete()
                return True, "Клиент успешно удален"
            elif record_class_name == "Couriers":
                # Проверяем, есть ли доставки у курьера
                deliveries_count = await Deliveries.filter(courier_id=record_id).count()
                if deliveries_count > 0:
                    return False, f"Невозможно удалить курьера: у него {deliveries_count} доставок"
                await record.delete()
                return True, "Курьер успешно удален"
            else:
                await record.delete()
                return True, "Запись успешно удалена"
            
        except IntegrityError as e:
            logger.warning(f"Ошибка целостности при удалении записи: {str(e)}")
            return False, "Невозможно удалить запись, так как на нее ссылаются другие данные"
        except Exception as e:
            logger.error(f"Ошибка удаления записи: {str(e)}")
            logger.error(traceback.format_exc())
            return False, f"Ошибка при удалении: {str(e)}"

    # =========================================================================
    # СПЕЦИАЛЬНЫЕ МЕТОДЫ ДЛЯ ПРИЛОЖЕНИЯ
    # =========================================================================
    @classmethod
    async def get_orders_statistics(cls):
        """Получение статистики по заказам"""
        try:
            orders = await Orders.all()
            total_orders = len(orders)
            
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT s.status_name, COUNT(o.order_id) as count
                FROM Orders o
                JOIN Statuses s ON o.status_id = s.status_id
                GROUP BY s.status_name
            """
            
            result = await connection.execute_query_dict(query)
            status_counts = {row['status_name']: row['count'] for row in result}
            
            deliveries = await Deliveries.all()
            delivered_count = len([d for d in deliveries if d.delivery_time is not None])
            
            stats = {
                'total_orders': total_orders,
                'status_counts': status_counts,
                'delivered_count': delivered_count,
                'delivery_rate': (delivered_count / total_orders * 100) if total_orders > 0 else 0
            }
            
            logger.debug(f"Статистика заказов получена: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Ошибка получения статистики заказов: {str(e)}")
            return {
                'total_orders': 0,
                'status_counts': {},
                'delivered_count': 0,
                'delivery_rate': 0
            }

    @classmethod
    async def get_popular_dishes(cls):
        """Получение популярных блюд"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT d.dish_id, d.name, d.restaurant_id, 
                    COALESCE(SUM(oi.quantity), 0) as total_quantity
                FROM Dishes d
                LEFT JOIN OrderItems oi ON d.dish_id = oi.dish_id
                GROUP BY d.dish_id, d.name, d.restaurant_id
                ORDER BY total_quantity DESC
                LIMIT 5
            """
            
            result = await connection.execute_query_dict(query)
            popular_dishes = []
            
            for row in result:
                dish_id = row['dish_id']
                dish = await Dishes.filter(dish_id=dish_id).first()
                restaurant = await Restaurants.filter(restaurant_id=row['restaurant_id']).first()
                
                if dish:
                    popular_dishes.append({
                        'dish': dish,
                        'restaurant': restaurant,
                        'order_count': int(row['total_quantity'])
                    })
            
            return popular_dishes
        except Exception as e:
            logger.error(f"Ошибка получения популярных блюд: {str(e)}")
            return []

    @classmethod
    async def get_dishes_by_restaurant(cls, restaurant_id):
        """Получение блюд по ресторану"""
        try:
            dishes = await Dishes.filter(restaurant_id=restaurant_id).all()
            return dishes
        except Exception as e:
            logger.error(f"Ошибка получения блюд ресторана: {str(e)}")
            return []

    @classmethod
    async def create_order_with_items(cls, customer_id, dish_quantities, courier_id=None):
        """Создание заказа с позициями"""
        try:
            # Создаем заказ
            order_data = {
                'customer_id': customer_id,
                'status_id': 1,  # Статус "Принят"
                'order_time': datetime.now()
            }
            order = await cls.create_record(Orders, **order_data)
            
            # Создаем позиции заказа
            for dish_id, quantity in dish_quantities:
                await OrderItems.create(
                    order_id=order.order_id,
                    dish_id=dish_id,
                    quantity=quantity
                )
            
            # Создаем доставку
            if courier_id:
                courier = await Couriers.filter(courier_id=courier_id).first()
            else:
                couriers = await Couriers.all()
                courier = couriers[0] if couriers else None
            
            if courier:
                delivery_data = {
                    'order_id': order.order_id,
                    'courier_id': courier.courier_id,
                    'delivery_time': None
                }
                await cls.create_record(Deliveries, **delivery_data)
            
            logger.info(f"Создан заказ #{order.order_id} с {len(dish_quantities)} позициями")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {str(e)}")
            raise

    @classmethod
    async def get_orders_with_details(cls):
        """Получение заказов с деталями"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT o.order_id, 
                    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
                    s.status_name,
                    o.order_time,
                    COUNT(oi.order_id) as items_count
                FROM Orders o
                LEFT JOIN Customers c ON o.customer_id = c.customer_id
                LEFT JOIN Statuses s ON o.status_id = s.status_id
                LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
                GROUP BY o.order_id, c.first_name, c.last_name, s.status_name, o.order_time
                ORDER BY o.order_time DESC
            """
            
            result = await connection.execute_query_dict(query)
            return result
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказов: {str(e)}")
            return []
    
    @classmethod
    async def get_order_details(cls, order_id):
        """Получение деталей конкретного заказа"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT 
                    o.order_id,
                    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
                    c.phone_number,
                    s.status_name,
                    o.order_time,
                    CONCAT(cr.first_name, ' ', cr.last_name) as courier_name,
                    cr.car_number,
                    d.delivery_time
                FROM Orders o
                LEFT JOIN Customers c ON o.customer_id = c.customer_id
                LEFT JOIN Statuses s ON o.status_id = s.status_id
                LEFT JOIN Deliveries d ON o.order_id = d.order_id
                LEFT JOIN Couriers cr ON d.courier_id = cr.courier_id
                WHERE o.order_id = %s
            """
            
            result = await connection.execute_query_dict(query, [order_id])
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Ошибка получения деталей заказа {order_id}: {str(e)}")
            return None

    @classmethod
    async def get_order_items(cls, order_id):
        """Получение позиций заказа"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT 
                    d.name as dish_name,
                    d.description,
                    d.cooking_time,
                    oi.quantity,
                    r.name as restaurant_name
                FROM OrderItems oi
                LEFT JOIN Dishes d ON oi.dish_id = d.dish_id
                LEFT JOIN Restaurants r ON d.restaurant_id = r.restaurant_id
                WHERE oi.order_id = %s
            """
            
            result = await connection.execute_query_dict(query, [order_id])
            logger.info(f"Получено {len(result)} позиций для заказа {order_id}")
            return result
        except Exception as e:
            logger.error(f"Ошибка получения позиций заказа {order_id}: {str(e)}")
            return []

    @classmethod
    async def get_customer_orders(cls, customer_id):
        """Получение заказов конкретного клиента"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            query = """
                SELECT 
                    o.order_id,
                    o.order_time,
                    s.status_name,
                    COUNT(oi.order_id) as items_count,
                    SUM(oi.quantity) as total_quantity
                FROM Orders o
                LEFT JOIN Statuses s ON o.status_id = s.status_id
                LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
                WHERE o.customer_id = %s
                GROUP BY o.order_id, o.order_time, s.status_name
                ORDER BY o.order_time DESC
            """
            
            result = await connection.execute_query_dict(query, [customer_id])
            return result
        except Exception as e:
            logger.error(f"Ошибка получения заказов клиента {customer_id}: {str(e)}")
            return []
    
    @classmethod
    async def debug_order_data(cls, order_id):
        """Отладочный метод для проверки данных заказа"""
        try:
            logger.info(f"=== ДЕБАГ ЗАКАЗА #{order_id} ===")
            
            # Проверяем существование заказа
            order = await Orders.filter(order_id=order_id).first()
            if not order:
                logger.info("Заказ не найден в таблице Orders")
                return
            
            logger.info(f"Заказ найден: {order.order_id}, клиент: {order.customer_id}, статус: {order.status_id}")
            
            # Проверяем клиента
            customer = await Customers.filter(customer_id=order.customer_id).first()
            logger.info(f"Клиент: {customer.first_name} {customer.last_name}" if customer else "Клиент не найден")
            
            # Проверяем статус
            status = await Statuses.filter(status_id=order.status_id).first()
            logger.info(f"Статус: {status.status_name}" if status else "Статус не найден")
            
            # Проверяем доставку
            delivery = await Deliveries.filter(order_id=order_id).first()
            if delivery:
                courier = await Couriers.filter(courier_id=delivery.courier_id).first()
                logger.info(f"Доставка: курьер {courier.first_name if courier else 'не найден'}, время: {delivery.delivery_time}")
            else:
                logger.info("Доставка не найдена")
                
            # Проверяем позиции заказа
            items = await cls.get_order_items(order_id)
            logger.info(f"Найдено позиций: {len(items)}")
            for item in items:
                logger.info(f"  - {item['dish_name']}: {item['quantity']} шт.")
                
            logger.info("=== КОНЕЦ ДЕБАГА ===")
            
        except Exception as e:
            logger.error(f"Ошибка в отладочном методе: {str(e)}")

    @classmethod
    async def check_database_structure(cls):
        """Проверка структуры базы данных"""
        try:
            from tortoise import connections
            connection = connections.get('default')
            
            # Проверяем существование таблиц
            tables = ['Orders', 'Customers', 'Statuses', 'Deliveries', 'Couriers', 'OrderItems', 'Dishes', 'Restaurants']
            
            for table in tables:
                check_query = f"SHOW TABLES LIKE '{table}'"
                result = await connection.execute_query_dict(check_query)
                logger.info(f"Таблица {table}: {'найдена' if result else 'не найдена'}")
                
        except Exception as e:
            logger.error(f"Ошибка проверки структуры БД: {str(e)}")
    
    @classmethod
    async def delete_order_cascade(cls, order_id):
        """Каскадное удаление заказа и связанных данных"""
        try:
            # Удаляем связанные записи в правильном порядке
            await Reviews.filter(order_id=order_id).delete()
            await Deliveries.filter(order_id=order_id).delete()
            await OrderItems.filter(order_id=order_id).delete()
            await Orders.filter(order_id=order_id).delete()
            
            logger.info(f"Заказ #{order_id} и все связанные данные удалены")
            return True, "Заказ и все связанные данные успешно удалены"
        except Exception as e:
            logger.error(f"Ошибка каскадного удаления заказа {order_id}: {str(e)}")
            return False, f"Ошибка при удалении заказа: {str(e)}"

    @classmethod
    async def delete_dish_cascade(cls, dish_id):
        """Каскадное удаление блюда и связанных данных"""
        try:
            # Проверяем, используется ли блюдо в заказах
            order_items_count = await OrderItems.filter(dish_id=dish_id).count()
            if order_items_count > 0:
                return False, f"Невозможно удалить блюдо: оно используется в {order_items_count} заказах"
            
            # Если блюдо не используется, удаляем его
            await Dishes.filter(dish_id=dish_id).delete()
            logger.info(f"Блюдо #{dish_id} удалено")
            return True, "Блюдо успешно удалено"
        except Exception as e:
            logger.error(f"Ошибка удаления блюда {dish_id}: {str(e)}")
            return False, f"Ошибка при удалении блюда: {str(e)}"

    @classmethod
    async def check_dependencies(cls, record):
        """Проверка зависимостей перед удалением"""
        try:
            record_class_name = record.__class__.__name__
            pk_name = record._meta.pk_attr
            record_id = getattr(record, pk_name)
            
            dependencies = []
            
            if record_class_name == "Orders":
                items_count = await OrderItems.filter(order_id=record_id).count()
                deliveries_count = await Deliveries.filter(order_id=record_id).count()
                reviews_count = await Reviews.filter(order_id=record_id).count()
                dependencies.append(f"Позиции заказа: {items_count}")
                dependencies.append(f"Доставки: {deliveries_count}")
                dependencies.append(f"Отзывы: {reviews_count}")
                
            elif record_class_name == "Dishes":
                items_count = await OrderItems.filter(dish_id=record_id).count()
                dependencies.append(f"Используется в заказах: {items_count} раз")
                
            elif record_class_name == "Restaurants":
                dishes_count = await Dishes.filter(restaurant_id=record_id).count()
                dependencies.append(f"Блюд в ресторане: {dishes_count}")
                
            elif record_class_name == "Customers":
                orders_count = await Orders.filter(customer_id=record_id).count()
                dependencies.append(f"Заказов у клиента: {orders_count}")
                
            elif record_class_name == "Couriers":
                deliveries_count = await Deliveries.filter(courier_id=record_id).count()
                dependencies.append(f"Доставок у курьера: {deliveries_count}")
            
            return dependencies
        except Exception as e:
            logger.error(f"Ошибка проверки зависимостей: {str(e)}")
            return [f"Ошибка при проверке зависимостей: {str(e)}"]
    
    @classmethod
    async def delete_restaurant_cascade(cls, restaurant_id):
        """Каскадное удаление ресторана и связанных данных"""
        try:
            # Получаем все блюда ресторана
            dishes = await Dishes.filter(restaurant_id=restaurant_id).all()
            
            # Проверяем, используются ли какие-либо блюда в заказах
            for dish in dishes:
                order_items_count = await OrderItems.filter(dish_id=dish.dish_id).count()
                if order_items_count > 0:
                    return False, f"Невозможно удалить ресторан: блюдо '{dish.name}' используется в {order_items_count} заказах"
            
            # Если блюда не используются, удаляем их и ресторан
            await Dishes.filter(restaurant_id=restaurant_id).delete()
            await Restaurants.filter(restaurant_id=restaurant_id).delete()
            
            logger.info(f"Ресторан #{restaurant_id} и все его блюда удалены")
            return True, "Ресторан и все его блюда успешно удалены"
        except Exception as e:
            logger.error(f"Ошибка удаления ресторана {restaurant_id}: {str(e)}")
            return False, f"Ошибка при удалении ресторана: {str(e)}"
