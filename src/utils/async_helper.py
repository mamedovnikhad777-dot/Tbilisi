"""
Простой помощник для работы с асинхронными операциями в Qt
"""

import logging
import asyncio
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


class AsyncWorker(QThread):
    """Рабочий поток для выполнения асинхронных задач"""
    
    task_completed = pyqtSignal(object)
    task_error = pyqtSignal(str)
    
    def __init__(self, coroutine_func, *args, **kwargs):
        super().__init__()
        self.coroutine_func = coroutine_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Запуск асинхронной задачи в потоке"""
        try:
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Запускаем корутину
                result = loop.run_until_complete(
                    self.coroutine_func(*self.args, **self.kwargs)
                )
                self.task_completed.emit(result)
            except Exception as e:
                logger.error(f"Ошибка в асинхронной задаче: {str(e)}", exc_info=True)
                self.task_error.emit(str(e))
            finally:
                # Закрываем все асинхронные ресурсы
                loop.close()
                
        except Exception as e:
            logger.error(f"Ошибка в потоке выполнения: {str(e)}", exc_info=True)
            self.task_error.emit(str(e))


class AsyncHelper(QObject):
    """Помощник для запуска асинхронных задач"""
    
    def __init__(self):
        super().__init__()
        self.active_workers = []
    
    def run_async(self, coroutine_func, on_complete=None, on_error=None, *args, **kwargs):
        """
        Запуск асинхронной задачи в отдельном потоке
        """
        worker = AsyncWorker(coroutine_func, *args, **kwargs)
        self.active_workers.append(worker)
        
        # Подключаем сигналы завершения
        if on_complete:
            worker.task_completed.connect(on_complete)
        
        if on_error:
            worker.task_error.connect(on_error)
        else:
            worker.task_error.connect(
                lambda error: logger.error(f"Ошибка в асинхронной задаче: {error}")
            )
        
        # Удаляем worker из списка при завершении
        def cleanup():
            if worker in self.active_workers:
                self.active_workers.remove(worker)
                worker.deleteLater()
        
        worker.task_completed.connect(cleanup)
        worker.task_error.connect(cleanup)
        worker.finished.connect(cleanup)
        
        # Запускаем поток
        worker.start()
        return worker
    
    def wait_all(self):
        """Ожидание завершения всех активных потоков"""
        for worker in self.active_workers[:]:
            if worker.isRunning():
                worker.wait()
    
    def cleanup(self):
        """Очистка всех активных потоков"""
        self.wait_all()
        self.active_workers.clear()


# Создаем глобальный экземпляр
async_helper = AsyncHelper()
