import threading
import time

from updater import ExchangeRateUpdater


class RateScheduler:
    def __init__(self, interval_hours = 24):
        self.interval = interval_hours * 3600  # в секундах
        self.updater = ExchangeRateUpdater()
        self.running = False
    
    def start(self):
        """Запустить периодическое обновление"""
        self.running = True
        print(f"Планировщик запущен. Обновление каждые {self.interval/3600} часов.")
        
        # Обновляем сразу при запуске
        self.updater.update_rates()
        
        # Запускаем фоновый поток
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()
    
    def _run(self):
        """Фоновый цикл обновления"""
        while self.running:
            time.sleep(self.interval)
            self.updater.update_rates()
    
    def stop(self):
        """Остановить планировщик"""
        self.running = False
        print("Планировщик остановлен")


def create_scheduler(interval_hours = 24):
    """Создать и вернуть экземпляр планировщика"""
    return RateScheduler(interval_hours)