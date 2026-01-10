from valutatrade_hub.infra.database import db


class ExchangeRateStorage:
    def __init__(self, filename="exchange_rates.json"):
        self.filename = filename
    
    def load_rates(self):
        """Загрузить курсы валют из файла"""
        return db.load(self.filename)
    
    def save_rates(self, rates):
        """Сохранить курсы валют в файл"""
        db.save(self.filename, rates)

def load_rates(filename="exchange_rates.json"):
    """Загрузить курсы валют из файла"""
    return db.load(filename)


def save_rates(rates, filename="exchange_rates.json"):
    """Сохранить курсы валют в файл"""
    db.save(filename, rates)