"""
Основная точка входа в приложение
"""

import sys
import os
import traceback

# Получаем путь к директории, в которой находится этот файл (src)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Поднимаемся на уровень выше (в корень проекта)
root_dir = os.path.dirname(current_dir)

# Добавляем корень проекта в sys.path, чтобы можно было импортировать модули из src
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Теперь можно импортировать модули из src
try:
    from src.sync_database import SyncDatabaseManager
    from src.ui.main_window import MainWindow
    from src.utils.config import setup_logging, get_db_config, print_db_config, check_env_file
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("\nТекущий sys.path:")
    for p in sys.path:
        print(f"  {p}")
    sys.exit(1)


def main():
    """Основная функция приложения"""
    try:
        # Проверяем наличие .env файла
        if not check_env_file():
            sys.exit(1)
        
        logger = setup_logging()
        logger.info("Запуск приложения управления доставкой еды")
        
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtGui import QPalette, QColor
        from PyQt6.QtCore import Qt
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Настройка темной темы
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        app.setPalette(dark_palette)
        
        app.setStyleSheet("""
            QToolTip { 
                color: #ffffff; 
                background-color: #2a82da; 
                border: 1px solid white; 
            }
            QTabWidget::pane { 
                border: 1px solid #555; 
                background-color: #353535; 
            }
            QTabBar::tab { 
                background-color: #555; 
                color: white; 
                padding: 8px; 
                margin: 2px; 
            }
            QTabBar::tab:selected { 
                background-color: #2a82da; 
            }
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #555; 
                border-radius: 5px; 
                margin-top: 1ex; 
                padding-top: 10px; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px 0 5px; 
            }
        """)
        
        # Получение конфигурации БД из переменных окружения
        print("\nЗагрузка конфигурации из переменных окружения...")
        try:
            db_config = get_db_config()
            print_db_config(db_config)
        except ValueError as e:
            print(f"❌ Ошибка конфигурации БД: {e}")
            print("\nУкажите настройки в файле .env или переменных окружения")
            sys.exit(1)
        
        # Инициализация базы данных
        print("\nИнициализация базы данных...")
        try:
            # Используем синхронный менеджер
            SyncDatabaseManager.init_db(db_config)
            print("✅ База данных успешно инициализирована")
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")
            logger.error(f"Ошибка инициализации БД: {e}", exc_info=True)
            
            # Показываем сообщение об ошибке
            QMessageBox.critical(
                None, 
                "Ошибка инициализации БД", 
                f"Не удалось подключиться к базе данных:\n{str(e)}\n\nПроверьте настройки подключения в файле .env"
            )
            sys.exit(1)
        
        # Создание главного окна
        main_window = MainWindow()
        logger.info("Приложение успешно инициализировано")
        
        # Отображение главного окна
        main_window.show()
        
        # Очистка при закрытии
        def cleanup():
            SyncDatabaseManager.close()
        
        app.aboutToQuit.connect(cleanup)
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
