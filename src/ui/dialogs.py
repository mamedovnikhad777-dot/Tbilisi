"""
Диалоговые окна приложения
"""

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QDialogButtonBox, QTextEdit, QComboBox, QDateEdit,
    QSpinBox, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from ..models import Customers, Restaurants, Dishes, Couriers, Orders, Statuses
from ..database_manager import DatabaseManager
from ..utils.async_helper import async_helper

logger = logging.getLogger(__name__)


class EditForm(QDialog):
    """Диалоговое окно для редактирования и добавления записей"""
    
    def __init__(self, model_class, record=None, parent=None):
        super().__init__(parent)
        self.model_class = model_class
        self.record = record
        self.setWindowTitle(f"Редактирование {model_class.__name__}")
        self.setModal(True)
        self.resize(500, 400)
        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        try:
            layout = QVBoxLayout(self)
            form_layout = QFormLayout()

            self.fields = {}
            model_name = self.model_class.__name__

            # Конфигурация полей для разных моделей
            if model_name == "Customers":
                self.setup_customer_fields(form_layout)
            elif model_name == "Restaurants":
                self.setup_restaurant_fields(form_layout)
            elif model_name == "Dishes":
                self.setup_dish_fields(form_layout)
            elif model_name == "Couriers":
                self.setup_courier_fields(form_layout)
            elif model_name == "Orders":
                self.setup_order_fields(form_layout)

            layout.addLayout(form_layout)

            # Кнопки OK и Cancel
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            button_box.accepted.connect(self.accept)
            button_box.rejected.connect(self.reject)
            layout.addWidget(button_box)
            
        except Exception as e:
            logger.error(f"Ошибка инициализации формы редактирования: {str(e)}")
            QMessageBox.critical(self, "Ошибка", "Не удалось загрузить форму редактирования")
            raise

    def setup_customer_fields(self, form_layout):
        """Настройка полей для клиентов"""
        self.fields['phone_number'] = QLineEdit()
        self.fields['first_name'] = QLineEdit()
        self.fields['last_name'] = QLineEdit()
        
        if self.record:
            self.fields['phone_number'].setText(self.record.phone_number)
            self.fields['first_name'].setText(self.record.first_name)
            self.fields['last_name'].setText(self.record.last_name)
        
        form_layout.addRow("Телефон:", self.fields['phone_number'])
        form_layout.addRow("Имя:", self.fields['first_name'])
        form_layout.addRow("Фамилия:", self.fields['last_name'])

    def setup_restaurant_fields(self, form_layout):
        """Настройка полей для ресторанов"""
        self.fields['name'] = QLineEdit()
        self.fields['location'] = QLineEdit()
        self.fields['rating'] = QDoubleSpinBox()
        self.fields['rating'].setRange(0, 5)
        self.fields['rating'].setDecimals(2)
        self.fields['rating'].setSingleStep(0.1)
        
        if self.record:
            self.fields['name'].setText(self.record.name)
            self.fields['location'].setText(self.record.location)
            self.fields['rating'].setValue(float(self.record.rating or 0))
        
        form_layout.addRow("Название:", self.fields['name'])
        form_layout.addRow("Адрес:", self.fields['location'])
        form_layout.addRow("Рейтинг:", self.fields['rating'])

    def setup_dish_fields(self, form_layout):
        """Настройка полей для блюд"""
        self.fields['name'] = QLineEdit()
        self.fields['description'] = QTextEdit()
        self.fields['description'].setMaximumHeight(100)
        
        # Исправление: используем QSpinBox для времени приготовления
        self.fields['cooking_time'] = QSpinBox()
        self.fields['cooking_time'].setRange(1, 300)  # от 1 до 300 минут
        self.fields['cooking_time'].setSuffix(" минут")
        
        self.fields['restaurant_id'] = QComboBox()
        
        # Загрузка ресторанов в комбобокс
        def load_restaurants():
            try:
                restaurants = async_helper.run_async(DatabaseManager.get_all(Restaurants))
                self.fields['restaurant_id'].clear()
                for restaurant in restaurants:
                    self.fields['restaurant_id'].addItem(f"{restaurant.name}", restaurant.restaurant_id)
            except Exception as e:
                logger.error(f"Ошибка загрузки ресторанов: {str(e)}")
        
        load_restaurants()
        
        if self.record:
            self.fields['name'].setText(self.record.name)
            self.fields['description'].setText(self.record.description or "")
            
            # Исправление: преобразование cooking_time в число
            try:
                cooking_time = str(self.record.cooking_time)
                # Если время в формате "00:25:00", извлекаем минуты
                if ':' in cooking_time:
                    time_parts = cooking_time.split(':')
                    minutes = int(time_parts[0]) * 60 + int(time_parts[1])
                    self.fields['cooking_time'].setValue(minutes)
                else:
                    # Если это просто число
                    self.fields['cooking_time'].setValue(int(cooking_time))
            except (ValueError, AttributeError):
                self.fields['cooking_time'].setValue(30)  # значение по умолчанию
                
            index = self.fields['restaurant_id'].findData(self.record.restaurant_id)
            if index >= 0:
                self.fields['restaurant_id'].setCurrentIndex(index)
        
        form_layout.addRow("Название:", self.fields['name'])
        form_layout.addRow("Описание:", self.fields['description'])
        form_layout.addRow("Время готовки (мин):", self.fields['cooking_time'])
        form_layout.addRow("Ресторан:", self.fields['restaurant_id'])

    def setup_courier_fields(self, form_layout):
        """Настройка полей для курьеров"""
        self.fields['phone_number'] = QLineEdit()
        self.fields['first_name'] = QLineEdit()
        self.fields['last_name'] = QLineEdit()
        self.fields['car_number'] = QLineEdit()
        
        if self.record:
            self.fields['phone_number'].setText(self.record.phone_number)
            self.fields['first_name'].setText(self.record.first_name)
            self.fields['last_name'].setText(self.record.last_name)
            self.fields['car_number'].setText(self.record.car_number)
        
        form_layout.addRow("Телефон:", self.fields['phone_number'])
        form_layout.addRow("Имя:", self.fields['first_name'])
        form_layout.addRow("Фамилия:", self.fields['last_name'])
        form_layout.addRow("Номер машины:", self.fields['car_number'])

    def setup_order_fields(self, form_layout):
        """Настройка полей для заказов"""
        self.fields['customer_id'] = QComboBox()
        self.fields['status_id'] = QComboBox()
        self.fields['order_time'] = QDateEdit()
        self.fields['order_time'].setCalendarPopup(True)
        self.fields['order_time'].setDate(QDate.currentDate())
        
        # Загрузка клиентов
        def load_customers():
            try:
                customers = async_helper.run_async(DatabaseManager.get_all(Customers))
                self.fields['customer_id'].clear()
                for customer in customers:
                    self.fields['customer_id'].addItem(f"{customer.first_name} {customer.last_name}", customer.customer_id)
            except Exception as e:
                logger.error(f"Ошибка загрузки клиентов: {str(e)}")
        
        # Загрузка статусов
        def load_statuses():
            try:
                statuses = async_helper.run_async(DatabaseManager.get_all(Statuses))
                self.fields['status_id'].clear()
                for status in statuses:
                    self.fields['status_id'].addItem(status.status_name, status.status_id)
            except Exception as e:
                logger.error(f"Ошибка загрузки статусов: {str(e)}")
        
        load_customers()
        load_statuses()
        
        if self.record:
            index = self.fields['customer_id'].findData(self.record.customer_id)
            if index >= 0: 
                self.fields['customer_id'].setCurrentIndex(index)
            index = self.fields['status_id'].findData(self.record.status_id)
            if index >= 0: 
                self.fields['status_id'].setCurrentIndex(index)
            if self.record.order_time:
                try:
                    order_date = QDate.fromString(str(self.record.order_time)[:10], "yyyy-MM-dd")
                    self.fields['order_time'].setDate(order_date)
                except:
                    self.fields['order_time'].setDate(QDate.currentDate())
        else:
            self.fields['order_time'].setDate(QDate.currentDate())
        
        form_layout.addRow("Клиент:", self.fields['customer_id'])
        form_layout.addRow("Статус:", self.fields['status_id'])
        form_layout.addRow("Дата заказа:", self.fields['order_time'])

    def get_data(self):
        """Получение данных из формы"""
        data = {}
        model_name = self.model_class.__name__
        
        if model_name == "Customers":
            data['phone_number'] = self.fields['phone_number'].text().strip()
            data['first_name'] = self.fields['first_name'].text().strip()
            data['last_name'] = self.fields['last_name'].text().strip()
            if not all([data['phone_number'], data['first_name'], data['last_name']]):
                raise ValueError("Все поля обязательны для заполнения")
        
        elif model_name == "Restaurants":
            data['name'] = self.fields['name'].text().strip()
            data['location'] = self.fields['location'].text().strip()
            if not data['name'] or not data['location']:
                raise ValueError("Название и адрес обязательны для заполнения")
            rating_value = self.fields['rating'].value()
            data['rating'] = rating_value if rating_value > 0 else None
        
        elif model_name == "Dishes":
            data['name'] = self.fields['name'].text().strip()
            data['cooking_time'] = str(self.fields['cooking_time'].value())  # Преобразуем в строку
            data['restaurant_id'] = self.fields['restaurant_id'].currentData()
            if not all([data['name'], data['cooking_time'], data['restaurant_id']]):
                raise ValueError("Все обязательные поля должны быть заполнены")
            data['description'] = self.fields['description'].toPlainText().strip() or None
        elif model_name == "Couriers":
            data['phone_number'] = self.fields['phone_number'].text().strip()
            data['first_name'] = self.fields['first_name'].text().strip()
            data['last_name'] = self.fields['last_name'].text().strip()
            data['car_number'] = self.fields['car_number'].text().strip()
            if not all([data['phone_number'], data['first_name'], data['last_name'], data['car_number']]):
                raise ValueError("Все поля обязательны для заполнения")
        
        elif model_name == "Orders":
            data['customer_id'] = self.fields['customer_id'].currentData()
            data['status_id'] = self.fields['status_id'].currentData()
            if not data['customer_id'] or not data['status_id']:
                raise ValueError("Клиент и статус обязательны для заполнения")
            order_date = self.fields['order_time'].date()
            order_time_str = order_date.toString("yyyy-MM-dd") + " 00:00:00"
            data['order_time'] = datetime.strptime(order_time_str, "%Y-%m-%d %H:%M:%S")
        
        return data

    def accept(self):
        """Переопределение accept для валидации данных"""
        try:
            self.get_data()
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка валидации", str(e))
        except Exception as e:
            logger.error(f"Ошибка при валидации данных: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")
