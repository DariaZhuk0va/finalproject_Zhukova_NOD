from valutatrade_hub.core.exceptions import CurrencyNotFoundError


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
        return (f"[CRYPTO] {self.code} — {self.name} "
                f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})")

def get_currency(code: str) -> Currency:
    """Получить валюту по коду"""
    code = code.upper()

    _currencies = {}

    _currencies["USD"] = Currency("US Dollar", "USD")   
    _currencies["EUR"] = Currency("Euro", "EUR")
    _currencies["GBP"] = Currency("British Pound", "GBP")
    _currencies["JPY"] = Currency("Japanese Yen", "JPY")
    _currencies["CHF"] = Currency("Swiss Franc", "CHF")
    _currencies["CAD"] = Currency("Canadian Dollar", "CAD")
    _currencies["AUD"] = Currency("Australian Dollar", "AUD")
    _currencies["CNY"] = Currency("Chinese Yuan", "CNY")
    _currencies["HKD"] = Currency("Hong Kong Dollar", "HKD")
    _currencies["SGD"] = Currency("Singapore Dollar", "SGD")
    _currencies["SEK"] = Currency("Swedish Krona", "SEK")
    _currencies["NOK"] = Currency("Norwegian Krone", "NOK")
    _currencies["KRW"] = Currency("South Korean Won", "KRW")
    _currencies["NZD"] = Currency("New Zealand Dollar", "NZD")
    _currencies["INR"] = Currency("Indian Rupee", "INR")
    _currencies["BRL"] = Currency("Brazilian Real", "BRL")
    _currencies["RUB"] = Currency("Russian Ruble", "RUB")
    _currencies["ZAR"] = Currency("South African Rand", "ZAR")
    _currencies["MXN"] = Currency("Mexican Peso", "MXN")
    _currencies["TRY"] = Currency("Turkish Lira", "TRY")
    _currencies["PLN"] = Currency("Polish Zloty", "PLN")
    _currencies["THB"] = Currency("Thai Baht", "THB")
    _currencies["IDR"] = Currency("Indonesian Rupiah", "IDR")
    _currencies["HUF"] = Currency("Hungarian Forint", "HUF")
    _currencies["CZK"] = Currency("Czech Koruna", "CZK")
    _currencies["ILS"] = Currency("Israeli New Shekel", "ILS")
    _currencies["CLP"] = Currency("Chilean Peso", "CLP")
    _currencies["PHP"] = Currency("Philippine Peso", "PHP")
    _currencies["AED"] = Currency("United Arab Emirates Dirham", "AED")
    _currencies["COP"] = Currency("Colombian Peso", "COP")
    _currencies["SAR"] = Currency("Saudi Riyal", "SAR")
    _currencies["MYR"] = Currency("Malaysian Ringgit", "MYR")
    _currencies["RON"] = Currency("Romanian Leu", "RON")
    _currencies["BTC"] = Currency("Bitcoin", "BTC")
    _currencies["ETH"] = Currency("Ethereum", "ETH")
    _currencies["BNB"] = Currency("Binance Coin", "BNB")
    _currencies["XRP"] = Currency("Ripple", "XRP")
    _currencies["SOL"] = Currency("Solana", "SOL")
    _currencies["DOGE"] = Currency("Dogecoin", "DOGE")
    _currencies["ADA"] = Currency("Cardano", "ADA")
    _currencies["AVAX"] = Currency("Avalanche", "AVAX")
    _currencies["DOT"] = Currency("Polkadot", "DOT")
    _currencies["TRX"] = Currency("TRON", "TRX")

    if code not in _currencies:
        raise CurrencyNotFoundError(code)

    return _currencies[code]
