"""
Виджеты пользовательского интерфейса
"""

import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QComboBox,
    QGroupBox, QListWidget, QListWidgetItem, QSpinBox,
    QSplitter, QFrame, QTextEdit, QFormLayout, QLineEdit,
    QDateEdit, QDoubleSpinBox, QCheckBox, QMessageBox,
    QHeaderView, QStackedWidget, QTabWidget, QMenuBar,
    QMenu, QDialog, QDialogButtonBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QFont, QAction, QPalette, QColor

from src.sync_database import SyncDatabaseManager  # Изменено на синхронный менеджер
from .dialogs import EditForm

logger = logging.getLogger(__name__)


class DataViewWidget(QWidget):
    """Виджет для отображения и управления данными таблиц"""
    
    def __init__(self, table_name, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.records = []
        self.init_ui()
        self.load_data()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout(self)

        # Панель инструментов
        toolbar_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_record)
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_record)
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_record)
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.load_data)

        toolbar_layout.addWidget(self.add_btn)
        toolbar_layout.addWidget(self.edit_btn)
        toolbar_layout.addWidget(self.delete_btn)
        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addStretch()

        layout.addLayout(toolbar_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных в таблицу"""
        try:
            logger.info(f"Загрузка данных для {self.table_name}")
            
            # Получаем данные синхронно
            if self.table_name == "Orders":
                self.records = SyncDatabaseManager.get_orders_with_details()
            else:
                self.records = SyncDatabaseManager.get_all(self.table_name)
            
            self.update_table()
            
        except Exception as e:
            logger.error(f"Ошибка загрузки данных для {self.table_name}: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def update_table(self):
        """Обновление таблицы данными"""
        try:
            if not self.records:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                return

            # Получаем названия столбцов из первой записи
            if self.records:
                columns = list(self.records[0].keys())
                self.table.setColumnCount(len(columns))
                self.table.setHorizontalHeaderLabels(columns)
                self.table.setRowCount(len(self.records))

                for row, record in enumerate(self.records):
                    for col, column_name in enumerate(columns):
                        value = record.get(column_name, "")
                        if value is None:
                            value = ""
                        self.table.setItem(row, col, QTableWidgetItem(str(value)))

                self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                logger.debug(f"Таблица {self.table_name} обновлена: {len(self.records)} записей")
            
        except Exception as e:
            logger.error(f"Ошибка обновления таблицы {self.table_name}: {str(e)}")

    def get_selected_record(self):
        """Получение выбранной записи"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.records):
            return self.records[current_row]
        return None

    def add_record(self):
        """Добавление новой записи"""
        QMessageBox.information(self, "Информация", "Функция добавления записи будет реализована в следующей версии")

    def edit_record(self):
        """Редактирование выбранной записи"""
        QMessageBox.information(self, "Информация", "Функция редактирования записи будет реализована в следующей версии")

    def delete_record(self):
        """Удаление выбранной записи"""
        QMessageBox.information(self, "Информация", "Функция удаления записи будет реализована в следующей версии")


class OrderCreationTab(QWidget):
    """Вкладка для создания новых заказов"""
    
    def __init__(self):
        super().__init__()
        self.selected_dishes = {}  # dish_id: quantity
        self.dishes_list = None
        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("Создание нового заказа")
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Выбор клиента
        customer_group = QGroupBox("Выбор клиента")
        customer_layout = QVBoxLayout(customer_group)
        self.customer_combo = QComboBox()
        self.load_customers()
        customer_layout.addWidget(self.customer_combo)
        layout.addWidget(customer_group)
        
        # Выбор курьера
        courier_group = QGroupBox("Выбор курьера")
        courier_layout = QVBoxLayout(courier_group)
        self.courier_combo = QComboBox()
        self.load_couriers()
        courier_layout.addWidget(self.courier_combo)
        layout.addWidget(courier_group)
        
        # Выбор ресторана и блюд
        dishes_group = QGroupBox("Выбор блюд")
        dishes_layout = QVBoxLayout(dishes_group)
        
        # Выбор ресторана
        restaurant_layout = QHBoxLayout()
        restaurant_layout.addWidget(QLabel("Ресторан:"))
        self.restaurant_combo = QComboBox()
        self.restaurant_combo.currentTextChanged.connect(self.load_restaurant_dishes)
        self.load_restaurants()
        restaurant_layout.addWidget(self.restaurant_combo)
        restaurant_layout.addStretch()
        dishes_layout.addLayout(restaurant_layout)
        
        # Список блюд
        dishes_layout.addWidget(QLabel("Доступные блюда:"))
        self.dishes_list = QListWidget()
        dishes_layout.addWidget(self.dishes_list)
        
        # Количество и кнопка добавления
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Количество:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10)
        self.quantity_spin.setValue(1)
        quantity_layout.addWidget(self.quantity_spin)
        
        self.add_dish_btn = QPushButton("Добавить в заказ")
        self.add_dish_btn.clicked.connect(self.add_dish_to_order)
        quantity_layout.addWidget(self.add_dish_btn)
        quantity_layout.addStretch()
        dishes_layout.addLayout(quantity_layout)
        
        layout.addWidget(dishes_group)
        
        # Выбранные блюда
        selected_group = QGroupBox("Текущий заказ")
        selected_layout = QVBoxLayout(selected_group)
        self.selected_dishes_table = QTableWidget()
        self.selected_dishes_table.setColumnCount(3)
        self.selected_dishes_table.setHorizontalHeaderLabels(["Блюдо", "Количество", "Действие"])
        self.selected_dishes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        selected_layout.addWidget(self.selected_dishes_table)
        layout.addWidget(selected_group)
        
        # Кнопка создания заказа
        self.create_order_btn = QPushButton("Оформить заказ")
        self.create_order_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;")
        self.create_order_btn.clicked.connect(self.create_order)
        layout.addWidget(self.create_order_btn)
        
        # Загрузка начальных данных
        if self.restaurant_combo.count() > 0:
            self.load_restaurant_dishes()

    def load_customers(self):
        """Загрузка списка клиентов"""
        try:
            self.customer_combo.clear()
            customers = SyncDatabaseManager.get_customers()
            for customer in customers:
                self.customer_combo.addItem(
                    f"{customer['first_name']} {customer['last_name']} ({customer['phone_number']})", 
                    customer['customer_id']
                )
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список клиентов")

    def load_couriers(self):
        """Загрузка списка курьеров"""
        try:
            self.courier_combo.clear()
            couriers = SyncDatabaseManager.get_couriers()
            for courier in couriers:
                self.courier_combo.addItem(
                    f"{courier['first_name']} {courier['last_name']} ({courier['car_number']})", 
                    courier['courier_id']
                )
        except Exception as e:
            logger.error(f"Ошибка загрузки курьеров: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список курьеров")

    def load_restaurants(self):
        """Загрузка списка ресторанов"""
        try:
            self.restaurant_combo.clear()
            restaurants = SyncDatabaseManager.get_restaurants()
            for restaurant in restaurants:
                self.restaurant_combo.addItem(
                    f"{restaurant['name']} - {restaurant['location']}", 
                    restaurant['restaurant_id']
                )
        except Exception as e:
            logger.error(f"Ошибка загрузки ресторанов: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список ресторанов")

    def load_restaurant_dishes(self):
        """Загрузка блюд выбранного ресторана"""
        try:
            if self.dishes_list is None:
                return
                
            self.dishes_list.clear()
            restaurant_id = self.restaurant_combo.currentData()
            if not restaurant_id:
                return
            
            dishes = SyncDatabaseManager.get_dishes_by_restaurant(restaurant_id)
            for dish in dishes:
                item_text = f"{dish['name']} - {dish['description'] or 'Нет описания'} - {dish['cooking_time']} мин"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, dish['dish_id'])
                self.dishes_list.addItem(item)
            
        except Exception as e:
            logger.error(f"Ошибка загрузки блюд: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить блюда ресторана")

    def add_dish_to_order(self):
        """Добавление блюда в заказ"""
        if self.dishes_list is None:
            return
            
        current_item = self.dishes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите блюдо из списка")
            return
            
        dish_id = current_item.data(Qt.ItemDataRole.UserRole)
        quantity = self.quantity_spin.value()
        
        # Получаем информацию о блюде
        try:
            dishes = SyncDatabaseManager.get_dishes()
            dish = next((d for d in dishes if d['dish_id'] == dish_id), None)
            if dish:
                self.selected_dishes[dish_id] = quantity
                self.update_selected_dishes_table(dishes)
                QMessageBox.information(self, "Успех", f"Блюдо '{dish['name']}' добавлено в заказ")
        
        except Exception as e:
            logger.error(f"Ошибка при получении блюд: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось получить информацию о блюде")

    def update_selected_dishes_table(self, dishes=None):
        """Обновление таблицы выбранных блюд"""
        if dishes is None:
            # Если блюда не переданы, загружаем их
            try:
                dishes_list = SyncDatabaseManager.get_dishes()
                dish_dict = {d['dish_id']: d for d in dishes_list}
                self._update_table_with_dishes(dish_dict)
            except Exception as e:
                logger.error(f"Ошибка загрузки блюд: {str(e)}")
        else:
            # Если блюда уже переданы, используем их
            dish_dict = {d['dish_id']: d for d in dishes}
            self._update_table_with_dishes(dish_dict)
    
    def _update_table_with_dishes(self, dish_dict):
        """Внутренний метод для обновления таблицы с блюдами"""
        self.selected_dishes_table.setRowCount(len(self.selected_dishes))
        
        for row, (dish_id, quantity) in enumerate(self.selected_dishes.items()):
            dish = dish_dict.get(dish_id)
            if dish:
                self.selected_dishes_table.setItem(row, 0, QTableWidgetItem(dish['name']))
                self.selected_dishes_table.setItem(row, 1, QTableWidgetItem(str(quantity)))
                
                # Кнопка удаления
                remove_btn = QPushButton("Удалить")
                remove_btn.clicked.connect(lambda checked, d_id=dish_id: self.remove_dish_from_order(d_id))
                self.selected_dishes_table.setCellWidget(row, 2, remove_btn)

    def remove_dish_from_order(self, dish_id):
        """Удаление блюда из заказа"""
        if dish_id in self.selected_dishes:
            del self.selected_dishes[dish_id]
            self.update_selected_dishes_table()

    def create_order(self):
        """Создание нового заказа"""
        if not self.selected_dishes:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одно блюдо в заказ")
            return
            
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
            
        courier_id = self.courier_combo.currentData()
        if not courier_id:
            QMessageBox.warning(self, "Ошибка", "Выберите курьера")
            return
            
        try:
            # Преобразуем словарь в список кортежей
            dish_quantities = [(dish_id, quantity) for dish_id, quantity in self.selected_dishes.items()]
            
            # Создаем заказ
            order_id = SyncDatabaseManager.create_order(customer_id, dish_quantities, courier_id)
            
            QMessageBox.information(self, "Успех", f"Заказ #{order_id} успешно создан!")
            
            # Очищаем форму
            self.selected_dishes.clear()
            self.selected_dishes_table.setRowCount(0)
            self.quantity_spin.setValue(1)
            
        except Exception as e:
            logger.error(f"Ошибка создания заказа: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать заказ: {str(e)}")

    def showEvent(self, event):
        """Обновление данных при показе вкладки"""
        self.refresh_data()
        super().showEvent(event)

    def refresh_data(self):
        """Обновление всех данных в форме"""
        try:
            self.load_customers()
            self.load_couriers()
            self.load_restaurants()
            if self.restaurant_combo.count() > 0:
                self.load_restaurant_dishes()
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {str(e)}")


class CustomerOrdersTab(QWidget):
    """Вкладка для просмотра заказов клиента"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel("📋 Мои заказы")
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Выбор клиента
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Выберите клиента:"))
        
        self.customer_combo = QComboBox()
        self.load_customers()
        self.customer_combo.currentTextChanged.connect(self.load_customer_orders)
        customer_layout.addWidget(self.customer_combo)
        
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_customer_orders)
        customer_layout.addWidget(refresh_btn)
        
        customer_layout.addStretch()
        layout.addLayout(customer_layout)
        
        # Таблица заказов
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(["ID заказа", "Время заказа", "Статус", "Кол-во позиций", "Общее количество"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.orders_table.doubleClicked.connect(self.show_order_details)
        layout.addWidget(self.orders_table)
        
        # Детали заказа
        details_group = QGroupBox("Детали заказа")
        details_layout = QVBoxLayout(details_group)
        
        # Информация о заказах
        self.order_info_label = QLabel("Выберите заказ для просмотра деталей")
        self.order_info_label.setWordWrap(True)
        details_layout.addWidget(self.order_info_label)
        
        # Таблица позиций заказа
        self.order_items_table = QTableWidget()
        self.order_items_table.setColumnCount(4)
        self.order_items_table.setHorizontalHeaderLabels(["Блюдо", "Описание", "Время готовки", "Количество"])
        self.order_items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        details_layout.addWidget(self.order_items_table)
        
        layout.addWidget(details_group)

    def load_customers(self):
        """Загрузка списка клиентов"""
        try:
            self.customer_combo.clear()
            customers = SyncDatabaseManager.get_customers()
            for customer in customers:
                self.customer_combo.addItem(
                    f"{customer['first_name']} {customer['last_name']} ({customer['phone_number']})", 
                    customer['customer_id']
                )
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить список клиентов")

    def load_customer_orders(self):
        """Загрузка заказов выбранного клиента"""
        try:
            customer_id = self.customer_combo.currentData()
            if not customer_id:
                return
            
            # Получаем все заказы с деталями
            orders_with_details = SyncDatabaseManager.get_orders_with_details()
            
            # Фильтруем заказы по клиенту
            customer_orders = []
            for order in orders_with_details:
                # Нам нужно определить customer_id из заказа
                # Для этого нужно получить customer_id из заказа
                # Поскольку в orders_with_details нет customer_id, используем другой подход
                
                # Альтернативный подход: получить заказы напрямую из базы
                import sqlalchemy as sa
                from sqlalchemy import text
                from src.sync_database import SyncDatabaseManager
                
                query = """
                    SELECT 
                        o.order_id,
                        o.order_time,
                        s.status_name,
                        COUNT(oi.order_id) as items_count,
                        COALESCE(SUM(oi.quantity), 0) as total_quantity
                    FROM Orders o
                    LEFT JOIN Statuses s ON o.status_id = s.status_id
                    LEFT JOIN OrderItems oi ON o.order_id = oi.order_id
                    WHERE o.customer_id = :customer_id
                    GROUP BY o.order_id, o.order_time, s.status_name
                    ORDER BY o.order_time DESC
                """
                
                connection = SyncDatabaseManager._connection
                result = connection.execute(text(query), {"customer_id": customer_id})
                
                orders = []
                for row in result:
                    orders.append({
                        'order_id': row[0],
                        'order_time': row[1],
                        'status_name': row[2],
                        'items_count': row[3],
                        'total_quantity': row[4]
                    })
                
                self.orders_table.setRowCount(len(orders))
                
                for row, order in enumerate(orders):
                    self.orders_table.setItem(row, 0, QTableWidgetItem(str(order['order_id'])))
                    self.orders_table.setItem(row, 1, QTableWidgetItem(str(order['order_time'])))
                    self.orders_table.setItem(row, 2, QTableWidgetItem(str(order['status_name'])))
                    self.orders_table.setItem(row, 3, QTableWidgetItem(str(order['items_count'])))
                    self.orders_table.setItem(row, 4, QTableWidgetItem(str(order['total_quantity'])))
                
                return
            
        except Exception as e:
            logger.error(f"Ошибка загрузки заказов клиента: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить заказы клиента")

    def show_order_details(self, index):
        """Показ деталей выбранного заказа"""
        try:
            row = index.row()
            order_id = int(self.orders_table.item(row, 0).text())
            
            # Загружаем детали заказа
            from src.sync_database import SyncDatabaseManager
            from sqlalchemy import text
            
            connection = SyncDatabaseManager._connection
            
            # Детали заказа
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
                WHERE o.order_id = :order_id
            """
            
            result = connection.execute(text(query), {"order_id": order_id})
            order_details = result.fetchone()
            
            if order_details:
                # Формируем информацию о заказе
                courier_info = f"{order_details[5] or 'Не назначен'} {order_details[6] or ''}"
                delivery_time = order_details[7] or 'Еще не доставлен'
                
                info_text = f"""
                <b>Заказ #{order_details[0]}</b><br>
                <b>Клиент:</b> {order_details[1]} ({order_details[2]})<br>
                <b>Статус:</b> {order_details[3]}<br>
                <b>Время заказа:</b> {order_details[4]}<br>
                <b>Курьер:</b> {courier_info}<br>
                <b>Время доставки:</b> {delivery_time}
                """
                self.order_info_label.setText(info_text)
            else:
                self.order_info_label.setText("Не удалось загрузить детали заказа")
            
            # Позиции заказа
            query = """
                SELECT 
                    d.name as dish_name,
                    d.description,
                    d.cooking_time,
                    oi.quantity
                FROM OrderItems oi
                LEFT JOIN Dishes d ON oi.dish_id = d.dish_id
                WHERE oi.order_id = :order_id
            """
            
            result = connection.execute(text(query), {"order_id": order_id})
            order_items = result.fetchall()
            
            self.order_items_table.setRowCount(len(order_items))
            for row, item in enumerate(order_items):
                self.order_items_table.setItem(row, 0, QTableWidgetItem(str(item[0])))
                self.order_items_table.setItem(row, 1, QTableWidgetItem(str(item[1] or 'Нет описания')))
                self.order_items_table.setItem(row, 2, QTableWidgetItem(str(item[2])))
                self.order_items_table.setItem(row, 3, QTableWidgetItem(str(item[3])))
            
        except Exception as e:
            logger.error(f"Ошибка загрузки деталей заказа: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить детали заказа")
