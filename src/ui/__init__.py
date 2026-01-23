"""
Модуль пользовательского интерфейса
"""

from .main_window import MainWindow
from .widgets import DataViewWidget, OrderCreationTab, CustomerOrdersTab
from .dialogs import EditForm

__all__ = [
    'MainWindow',
    'DataViewWidget',
    'OrderCreationTab',
    'CustomerOrdersTab',
    'EditForm',
]
