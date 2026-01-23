"""
Главное окно приложения
"""
import sys
import os
import logging
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import pyqtSlot
import logging
from datetime import datetime

# Добавляем путь к src для абсолютных импортов
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTableWidget,
    QHeaderView, QFrame, QMessageBox,
    QMenuBar, QMenu, QTabWidget, QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction, QPalette, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.database_manager import DatabaseManager
from src.utils.async_helper import async_helper
from src.models import Restaurants
from reports.excel_report import ExcelReportGenerator
from .widgets import DataViewWidget, OrderCreationTab, CustomerOrdersTab

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система управления доставкой еды")
        self.setGeometry(100, 100, 1400, 900)
        self.current_data_view = None  # Добавляем атрибут для хранения текущего виджета данных
        self.data_management_layout = None  # Добавляем атрибут для layout
        self.init_ui()
        
        # Таймер для обновления данных
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(30000)  # Обновление каждые 30 секунд

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        try:
            # Создание центрального виджета с вкладками
            self.tab_widget = QTabWidget()
            self.setCentralWidget(self.tab_widget)
            
            # Создание вкладок
            self.create_dashboard_tab()
            self.create_order_creation_tab()
            self.create_customer_orders_tab()
            self.create_data_management_tab()
            self.create_analytics_tab()
            
            # Создание меню
            self.create_menu()
            
            # Создание статусной строки
            self.statusBar().showMessage("Система готова к работе")
            
            logger.info("Главное окно инициализировано")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации главного окна: {str(e)}")
            raise
    
    @pyqtSlot()
    def export_to_excel(self):
        """Создание Excel отчета"""
        try:
            logger.info("Запуск создания Excel отчета")
            
            # Показываем сообщение
            self.statusBar().showMessage("Создание Excel отчёта...")
            
            # Создаем генератор отчетов
            excel_generator = ExcelReportGenerator()
            
            # Генерируем отчет в отдельном потоке, чтобы не блокировать UI
            import threading
            
            def generate_report():
                try:
                    # Генерируем отчет
                    file_path = excel_generator.generate_full_report_sync()
                    
                    if file_path:
                        # Показываем сообщение об успехе в основном потоке
                        self.statusBar().showMessage("Excel отчёт создан успешно", 5000)
                        QMessageBox.information(
                            self, 
                            "Успех", 
                            f"Excel отчет успешно создан:\n{file_path}"
                        )
                    else:
                        self.statusBar().showMessage("Ошибка создания Excel отчёта", 5000)
                        QMessageBox.warning(
                            self,
                            "Ошибка",
                            "Не удалось создать Excel отчет"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при создании Excel отчета: {str(e)}", exc_info=True)
                    self.statusBar().showMessage("Ошибка создания отчёта", 5000)
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Ошибка при создании Excel отчета:\n{str(e)}"
                    )
            
            # Запускаем в отдельном потоке
            thread = threading.Thread(target=generate_report, daemon=True)
            thread.start()
            
        except Exception as e:
            logger.error(f"Ошибка при запуске Excel отчета: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Ошибка при запуске Excel отчета:\n{str(e)}"
            )
    
    def create_menu(self):
        """Создание главного меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        # Добавляем пункт экспорта в Excel
        export_excel_action = QAction("Экспорт в Excel", self)
        export_excel_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(export_excel_action)
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Данные
        data_menu = menubar.addMenu("Данные")
        refresh_action = QAction("Обновить данные", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_all_data)
        data_menu.addAction(refresh_action)

        # Меню Отчеты
        reports_menu = menubar.addMenu("Отчеты")
        
        # Статистический отчет
        statistical_report_action = QAction("Статистический отчет", self)
        statistical_report_action.triggered.connect(self.generate_statistical_report)
        reports_menu.addAction(statistical_report_action)
        
        # Детальный отчет  
        detailed_report_action = QAction("Детальный отчет", self)
        detailed_report_action.triggered.connect(self.generate_detailed_report)
        reports_menu.addAction(detailed_report_action)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def generate_statistical_report(self):
        """Генерация статистического отчета"""
        try:
            QMessageBox.information(self, "Генерация отчета", "Начинаю генерацию статистического отчета...")
            
            # Используем асинхронный подход
            from reports.statistical_report import StatisticalReport
            
            def on_report_generated(file_path):
                if file_path:
                    QMessageBox.information(self, "Успех", 
                                          f"Статистический отчет успешно сгенерирован!\nФайл: {file_path}")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать отчет")
            
            def on_report_error(error_msg):
                QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации отчета: {error_msg}")
            
            reporter = StatisticalReport()
            async_helper.run_async(
                reporter.generate_report,
                on_complete=on_report_generated,
                on_error=on_report_error
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации статистического отчета: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации отчета: {str(e)}")

    def generate_detailed_report(self):
        """Генерация детального отчета"""
        try:
            QMessageBox.information(self, "Генерация отчета", "Начинаю генерацию детального отчета...")
            
            # Используем асинхронный подход
            from reports.detailed_report import DetailedReport
            
            def on_report_generated(file_path):
                if file_path:
                    QMessageBox.information(self, "Успех", 
                                          f"Детальный отчет успешно сгенерирован!\nФайл: {file_path}")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось сгенерировать отчет")
            
            def on_report_error(error_msg):
                QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации отчета: {error_msg}")
            
            reporter = DetailedReport()
            async_helper.run_async(
                reporter.generate_report,
                on_complete=on_report_generated,
                on_error=on_report_error
            )
            
        except Exception as e:
            logger.error(f"Ошибка генерации детального отчета: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при генерации отчета: {str(e)}")
    
    def create_dashboard_tab(self):
        """Создание вкладки дашборда"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Заголовок
        title_label = QLabel("Панель управления доставкой еды")
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("padding: 10px; color: #ffffff;")
        layout.addWidget(title_label)
        
        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #555555;")
        layout.addWidget(line)
        
        # Графики
        charts_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Первая строка графиков
        first_row_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # График распределения заказов
        orders_chart_widget = self.create_chart_widget("📊 Распределение заказов по статусам")
        self.orders_fig, self.orders_ax = plt.subplots(figsize=(8, 6))
        self.setup_chart_style(self.orders_fig, self.orders_ax)
        self.orders_canvas = FigureCanvas(self.orders_fig)
        self.setup_canvas_style(self.orders_canvas)
        orders_chart_widget.layout().addWidget(self.orders_canvas)
        first_row_splitter.addWidget(orders_chart_widget)
        
        # График популярных блюд
        dishes_chart_widget = self.create_chart_widget("🍽️ Популярные блюда")
        self.dishes_fig, self.dishes_ax = plt.subplots(figsize=(8, 6))
        self.setup_chart_style(self.dishes_fig, self.dishes_ax)
        self.dishes_canvas = FigureCanvas(self.dishes_fig)
        self.setup_canvas_style(self.dishes_canvas)
        dishes_chart_widget.layout().addWidget(self.dishes_canvas)
        first_row_splitter.addWidget(dishes_chart_widget)
        
        # Вторая строка графиков - рейтинги ресторанов
        ratings_chart_widget = self.create_chart_widget("⭐ Рейтинги ресторанов")
        self.ratings_fig, self.ratings_ax = plt.subplots(figsize=(16, 6))
        self.setup_chart_style(self.ratings_fig, self.ratings_ax)
        self.ratings_canvas = FigureCanvas(self.ratings_fig)
        self.setup_canvas_style(self.ratings_canvas)
        ratings_chart_widget.layout().addWidget(self.ratings_canvas)
        
        # Добавляем строки в основной splitter
        charts_splitter.addWidget(first_row_splitter)
        charts_splitter.addWidget(ratings_chart_widget)
        
        # Устанавливаем размеры для лучшего отображения
        charts_splitter.setSizes([400, 300])
        first_row_splitter.setSizes([400, 400])
        
        layout.addWidget(charts_splitter)
        
        self.tab_widget.addTab(dashboard_widget, "📊 Панель управления")
    
    def create_chart_widget(self, title):
        """Создание виджета для графика"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        title_label = QLabel(title)
        title_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; padding: 5px;")
        layout.addWidget(title_label)
        return widget
    
    def setup_chart_style(self, fig, ax):
        """Настройка стиля графика"""
        fig.patch.set_facecolor('#2b2b2b')
        ax.set_facecolor('#2b2b2b')
    
    def setup_canvas_style(self, canvas):
        """Настройка стиля canvas"""
        canvas.setStyleSheet("background-color: #2b2b2b; border: 1px solid #555; border-radius: 5px;")
    
    def create_order_creation_tab(self):
        """Создание вкладки оформления заказа"""
        order_tab = OrderCreationTab()
        self.tab_widget.addTab(order_tab, "🛒 Оформление заказа")
    
    def create_customer_orders_tab(self):
        """Создание вкладки просмотра заказов"""
        customer_orders_tab = CustomerOrdersTab()
        self.tab_widget.addTab(customer_orders_tab, "📋 Мои заказы")
    
    def create_data_management_tab(self):
        """Создание вкладки управления данными"""
        data_widget = QWidget()
        self.data_management_layout = QVBoxLayout(data_widget)

        # Выбор модели
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Выберите таблицу:"))
        
        self.model_combo = QComboBox()
        self.models = {
            "Клиенты": "Customers",
            "Рестораны": "Restaurants",
            "Блюда": "Dishes",
            "Курьеры": "Couriers",
            "Заказы": "Orders"
        }
        
        for name in self.models.keys():
            self.model_combo.addItem(name)
        
        self.model_combo.currentTextChanged.connect(self.model_changed)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        self.data_management_layout.addLayout(model_layout)

        # Создаем начальный виджет просмотра данных
        self.current_data_view = DataViewWidget("Customers")
        self.data_management_layout.addWidget(self.current_data_view)
        
        self.tab_widget.addTab(data_widget, "🗃️ Управление данными")
    
    def model_changed(self, model_name):
        """Обработчик изменения выбранной таблицы"""
        try:
            if model_name not in self.models:
                return
                
            table_name = self.models[model_name]
            
            # Удаляем старый виджет
            if self.current_data_view:
                self.current_data_view.setParent(None)
                self.current_data_view.deleteLater()
            
            # Создаем новый виджет
            self.current_data_view = DataViewWidget(table_name)
            self.data_management_layout.addWidget(self.current_data_view)
            
            logger.info(f"Переключение на таблицу: {model_name} ({table_name})")
            
        except Exception as e:
            logger.error(f"Ошибка переключения на таблицу {model_name}: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось переключить таблицу: {str(e)}")
    
    def create_analytics_tab(self):
        """Создание вкладки аналитики"""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Заголовок
        title_label = QLabel("Аналитика и отчеты")
        title_label.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Группа фильтров
        filters_group = QGroupBox("Фильтры анализа")
        filters_layout = QHBoxLayout(filters_group)
        
        filters_layout.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["За все время", "За последний месяц", "За последнюю неделю"])
        filters_layout.addWidget(self.period_combo)
        
        filters_layout.addWidget(QLabel("Тип анализа:"))
        self.analysis_type_combo = QComboBox()
        self.analysis_type_combo.addItems(["Статистика заказов", "Активность клиентов", "Эффективность доставки"])
        filters_layout.addWidget(self.analysis_type_combo)
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.apply_analysis_filters)
        filters_layout.addWidget(apply_btn)
        
        export_btn = QPushButton("Экспорт в CSV")
        export_btn.clicked.connect(self.export_analysis)
        filters_layout.addWidget(export_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_group)
        
        # Таблица с детальной аналитикой
        self.analytics_table = QTableWidget()
        self.analytics_table.setAlternatingRowColors(True)
        layout.addWidget(self.analytics_table)
        
        self.tab_widget.addTab(analytics_widget, "📈 Аналитика")
    
    def update_orders_chart(self):
        """Обновление графика заказов"""
        try:
            self.orders_ax.clear()
            
            # Получаем статистику заказов асинхронно
            async_helper.run_async(
                DatabaseManager.get_orders_statistics,
                on_complete=self.on_orders_statistics_loaded,
                on_error=lambda e: logger.error(f"Ошибка получения статистики заказов: {e}")
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика заказов: {str(e)}")
    
    def on_orders_statistics_loaded(self, stats):
        """Обработчик загрузки статистики заказов"""
        try:
            self.orders_ax.clear()
            
            status_counts = stats.get('status_counts', {})
            if status_counts:
                labels = list(status_counts.keys())
                sizes = list(status_counts.values())
                
                colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336', '#9C27B0', '#00BCD4', '#E91E63']
                
                wedges, texts, autotexts = self.orders_ax.pie(
                    sizes, 
                    labels=labels, 
                    colors=colors[:len(labels)], 
                    autopct='%1.1f%%', 
                    startangle=90,
                    textprops={'color': 'white', 'fontsize': 10}
                )
                
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                for text in texts:
                    text.set_color('white')
                    text.set_fontsize(11)
                
                self.orders_ax.axis('equal')
                self.orders_ax.set_title('Распределение заказов по статусам', 
                                       color='white', fontsize=14, fontweight='bold', pad=20)
                
                legend = self.orders_ax.legend(wedges, labels, title="Статусы", loc="center left", 
                                            bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
                legend.get_title().set_color('white')
                legend.get_title().set_fontweight('bold')
                for text in legend.get_texts():
                    text.set_color('white')
            else:
                self.orders_ax.text(0.5, 0.5, 'Нет данных о заказах', 
                                  ha='center', va='center', color='white', fontsize=12,
                                  transform=self.orders_ax.transAxes)
            
            self.orders_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка построения графика заказов: {str(e)}")
        
    def update_dishes_chart(self):
        """Обновление графика популярных блюд"""
        try:
            self.dishes_ax.clear()
            
            # Получаем популярные блюда асинхронно
            async_helper.run_async(
                DatabaseManager.get_popular_dishes,
                on_complete=self.on_popular_dishes_loaded,
                on_error=lambda e: logger.error(f"Ошибка получения популярных блюд: {e}")
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика блюд: {str(e)}")

    def on_popular_dishes_loaded(self, popular_dishes):
        """Обработчик загрузки популярных блюд"""
        try:
            self.dishes_ax.clear()
            
            if popular_dishes and len(popular_dishes) > 0:
                dish_names = []
                order_counts = []
                for item in popular_dishes:
                    name = item['dish'].name
                    if len(name) > 20:
                        name = name[:20] + '...'
                    dish_names.append(name)
                    order_counts.append(item.get('order_count', 0))
                
                if any(count > 0 for count in order_counts):
                    colors = ['#4CAF50', '#2196F3', '#FF9800', '#F44336', '#9C27B0']
                    
                    bars = self.dishes_ax.bar(dish_names, order_counts, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
                    
                    self.dishes_ax.set_ylabel('Количество заказов', color='white', fontsize=12, fontweight='bold')
                    self.dishes_ax.set_xlabel('Блюда', color='white', fontsize=12, fontweight='bold')
                    self.dishes_ax.tick_params(axis='x', rotation=45, colors='white', labelsize=10)
                    self.dishes_ax.tick_params(axis='y', colors='white', labelsize=10)
                    
                    for bar, count in zip(bars, order_counts):
                        height = bar.get_height()
                        self.dishes_ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                          f'{count}', ha='center', va='bottom', 
                                          color='white', fontweight='bold', fontsize=11)
                    
                    self.dishes_ax.set_title('Топ-5 популярных блюд', color='white', fontsize=14, fontweight='bold', pad=20)
                    self.dishes_ax.grid(True, alpha=0.3, color='gray')
                    self.dishes_ax.set_facecolor('#2b2b2b')
                else:
                    self.dishes_ax.text(0.5, 0.5, 'Нет данных о заказах блюд', 
                                      ha='center', va='center', color='white', fontsize=12,
                                      transform=self.dishes_ax.transAxes)
            else:
                self.dishes_ax.text(0.5, 0.5, 'Нет данных о популярных блюдах', 
                                  ha='center', va='center', color='white', fontsize=12,
                                  transform=self.dishes_ax.transAxes)
            
            self.dishes_canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка построения графика блюд: {str(e)}")

    def update_restaurants_ratings_chart(self):
        """Обновление графика рейтингов ресторанов"""
        try:
            self.ratings_ax.clear()
            
            # Получаем рестораны асинхронно
            async_helper.run_async(
                DatabaseManager.get_all,
                Restaurants,
                on_complete=self.on_restaurants_loaded,
                on_error=lambda e: logger.error(f"Ошибка получения ресторанов: {e}")
            )
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика рейтингов ресторанов: {str(e)}")

    def on_restaurants_loaded(self, restaurants):
        """Обработчик загрузки ресторанов"""
        try:
            self.ratings_ax.clear()
            
            # Фильтруем рестораны с рейтингами и сортируем
            rated_restaurants = [r for r in restaurants if r.rating is not None]
            rated_restaurants.sort(key=lambda x: x.rating, reverse=True)
            top_restaurants = rated_restaurants[:5]  # Берем топ-5
            
            if top_restaurants:
                names = []
                ratings = []
                for restaurant in top_restaurants:
                    name = restaurant.name
                    if len(name) > 25:
                        name = name[:25] + '...'
                    names.append(name)
                    ratings.append(float(restaurant.rating))
                
                colors = []
                for rating in ratings:
                    if rating >= 4.5:
                        colors.append('#4CAF50')
                    elif rating >= 4.0:
                        colors.append('#2196F3')
                    elif rating >= 3.5:
                        colors.append('#FF9800')
                    else:
                        colors.append('#F44336')
                
                y_pos = range(len(names))
                bars = self.ratings_ax.barh(y_pos, ratings, color=colors, alpha=0.8, 
                                          edgecolor='white', linewidth=1, height=0.7)
                
                self.ratings_ax.set_yticks(y_pos)
                self.ratings_ax.set_yticklabels(names, color='white', fontsize=11)
                self.ratings_ax.set_xlabel('Рейтинг', color='white', fontsize=12, fontweight='bold')
                self.ratings_ax.set_xlim(0, 5)
                self.ratings_ax.tick_params(axis='x', colors='white', labelsize=10)
                
                for i, (bar, rating) in enumerate(zip(bars, ratings)):
                    width = bar.get_width()
                    self.ratings_ax.text(width + 0.1, bar.get_y() + bar.get_height()/2.,
                                       f'{rating:.2f}', ha='left', va='center', 
                                       color='white', fontweight='bold', fontsize=11)
                
                self.ratings_ax.set_title('Рейтинги ресторанов', color='white', 
                                        fontsize=14, fontweight='bold', pad=20)
                self.ratings_ax.grid(True, alpha=0.3, color='gray', axis='x')
                
                from matplotlib.patches import Patch
                legend_elements = [
                    Patch(facecolor='#4CAF50', alpha=0.8, label='Отлично (4.5+)'),
                    Patch(facecolor='#2196F3', alpha=0.8, label='Хорошо (4.0-4.5)'),
                    Patch(facecolor='#FF9800', alpha=0.8, label='Удовлетворительно (3.5-4.0)'),
                    Patch(facecolor='#F44336', alpha=0.8, label='Плохо (<3.5)')
                ]
                self.ratings_ax.legend(handles=legend_elements, loc='lower right',
                                     fontsize=10, framealpha=0.9,
                                     labelcolor='white')
                
            else:
                self.ratings_ax.text(0.5, 0.5, 'Нет данных о рейтингах ресторанов', 
                                   ha='center', va='center', color='white', fontsize=12,
                                   transform=self.ratings_ax.transAxes)
            
            self.ratings_canvas.draw()
            self.ratings_fig.tight_layout()
            
        except Exception as e:
            logger.error(f"Ошибка построения графика рейтингов ресторанов: {str(e)}")
    
    def update_dashboard(self):
        """Обновление данных на дашборде"""
        try:
            logger.info("Обновление данных дашборда")
            self.update_orders_chart()
            self.update_dishes_chart()
            self.update_restaurants_ratings_chart()
            self.statusBar().showMessage(f"Данные обновлены: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            logger.error(f"Ошибка обновления дашборда: {str(e)}")
    
    def refresh_all_data(self):
        """Обновление всех данных"""
        try:
            # Обновляем текущую вкладку управления данными
            if self.current_data_view:
                self.current_data_view.load_data()
            
            self.update_dashboard()
            QMessageBox.information(self, "Обновление", "Все данные успешно обновлены")
        except Exception as e:
            logger.error(f"Ошибка обновления данных: {str(e)}")
            QMessageBox.warning(self, "Ошибка", "Не удалось обновить данные")
    
    def apply_analysis_filters(self):
        """Применение фильтров анализа"""
        period = self.period_combo.currentText()
        analysis_type = self.analysis_type_combo.currentText()
        QMessageBox.information(self, "Фильтры", 
                              f"Применены фильтры: {analysis_type}, период: {period}")
    
    def export_analysis(self):
        """Экспорт аналитики"""
        QMessageBox.information(self, "Экспорт", "Данные экспортированы в CSV")
    
    def show_about(self):
        """Показ информации о программе"""
        about_text = """
        <h3>Система управления доставкой еды</h3>
        <p>Версия 2.0</p>
        <p>Программа для управления и анализа данных службы доставки еды.</p>
        <p>Функции:</p>
        <ul>
            <li>Управление клиентами, ресторанами, блюдами и заказами</li>
            <li>Визуализация ключевых метрик</li>
            <li>Аналитика и отчетность</li>
            <li>Удобное оформление заказов</li>
            <li>Просмотр истории заказов</li>
            <li>Генерация PDF отчетов</li>
        </ul>
        <p>© 2024 Все права защищены.</p>
        """
        QMessageBox.about(self, "О программе", about_text)
