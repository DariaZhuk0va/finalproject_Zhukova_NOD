class Currency:
    """Базовый класс для валют с публичными атрибутами"""
    
    def __init__(self, name: str, code: str):
        name = name.strip()
        code = code.strip()
        
        if not name:
            raise ValueError("Имя валюты не может быть пустым")
        self.name = name
        
        if not code:
            raise ValueError("Код валюты не может быть пустым")
        if code != code.upper():
            raise ValueError("Код валюты должен быть в ВЕРХНЕМ регистре")
        if len(code) < 2:
            raise ValueError("Код валюты должен быть не менее 2 символов")
        if len(code) > 5:
            raise ValueError("Код валюты должен быть не более 5 символов")
        if " " in code:
            raise ValueError("Код валюты не должен содержать пробелов")
        if not code.isalnum():
            raise ValueError("Код валюты должен содержать только буквы и цифры")
        self.code = code
    
    def get_display_info(self) -> str:
        """Строковое представление для UI/логов"""
        return f"{self.code} — {self.name}"

class FiatCurrency(Currency):
    """Фиатная валюта с публичным атрибутом issuing_country"""
    
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country
    
    def get_display_info(self) -> str:
        """Переопределение метода"""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"
    
class CryptoCurrency(Currency):
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float = 0.0):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
    
    def get_display_info(self):
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"

class CurrencyNotFoundError(Exception):
    pass

def get_currency(code: str) -> Currency:
    """Получить валюту по коду"""
    code = code.upper()
    
    _currencies = {}

    _currencies["USD"] = Currency("US Dollar", "USD")
    _currencies["EUR"] = Currency("Euro", "EUR")  
    _currencies["RUB"] = Currency("Russian Ruble", "RUB")
    _currencies["BTC"] = Currency("Bitcoin", "BTC")
    _currencies["ETH"] = Currency("Ethereum", "ETH")

    if code not in _currencies:
        raise CurrencyNotFoundError(f"Валюта '{code}' не найдена")
    
    return _currencies[code]


