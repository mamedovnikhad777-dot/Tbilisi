"""
Модели базы данных Tortoise ORM
"""

from tortoise import fields
from tortoise.models import Model


class Statuses(Model):
    """Модель статусов заказов"""
    status_id = fields.IntField(pk=True)
    status_name = fields.CharField(max_length=50, unique=True)

    class Meta:
        table = "Statuses"


class Customers(Model):
    """Модель клиентов"""
    customer_id = fields.IntField(pk=True)
    phone_number = fields.CharField(max_length=20, unique=True)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)

    class Meta:
        table = "Customers"


class Restaurants(Model):
    """Модель ресторанов"""
    restaurant_id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    location = fields.CharField(max_length=500)
    rating = fields.DecimalField(max_digits=3, decimal_places=2, null=True)

    class Meta:
        table = "Restaurants"


class Dishes(Model):
    """Модель блюд"""
    dish_id = fields.IntField(pk=True)
    restaurant_id = fields.IntField()
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    cooking_time = fields.CharField(max_length=20)

    class Meta:
        table = "Dishes"


class Couriers(Model):
    """Модель курьеров"""
    courier_id = fields.IntField(pk=True)
    phone_number = fields.CharField(max_length=20, unique=True)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    car_number = fields.CharField(max_length=20, unique=True)

    class Meta:
        table = "Couriers"


class Orders(Model):
    """Модель заказов"""
    order_id = fields.IntField(pk=True)
    customer_id = fields.IntField()
    status_id = fields.IntField()
    order_time = fields.DatetimeField()

    class Meta:
        table = "Orders"


class OrderItems(Model):
    """Модель позиций заказа"""
    order_id = fields.IntField()
    dish_id = fields.IntField()
    quantity = fields.IntField(default=1)

    class Meta:
        table = "OrderItems"
        unique_together = (("order_id", "dish_id"),)


class Deliveries(Model):
    """Модель доставок"""
    delivery_id = fields.IntField(pk=True)
    order_id = fields.IntField()
    courier_id = fields.IntField()
    delivery_time = fields.DatetimeField(null=True)

    class Meta:
        table = "Deliveries"


class Reviews(Model):
    """Модель отзывов"""
    review_id = fields.IntField(pk=True)
    order_id = fields.IntField()
    rating = fields.IntField()
    description = fields.TextField(null=True)

    class Meta:
        table = "Reviews"


# Экспорт всех моделей
__all__ = [
    'Statuses',
    'Customers',
    'Restaurants',
    'Dishes',
    'Couriers',
    'Orders',
    'OrderItems',
    'Deliveries',
    'Reviews',
]
