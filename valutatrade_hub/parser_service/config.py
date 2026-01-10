import os
from dataclasses import dataclass

from valutatrade_hub.infra.settings import settings
from dotenv import load_dotenv


load_dotenv()

@dataclass
class ParserConfig:
    def __init__(self):
        # Криптовалюты и их ID для CoinGecko API
        self.CRYPTO_ID_MAP = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "SOL": "solana",
            "DOGE": "dogecoin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "TRX": "tron",
        }
        
        # Фиатные валюты для ExchangeRate-API
        self.FIAT_CURRENCIES = [
            "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "HKD", 
            "SGD", "SEK", "NOK", "KRW", "NZD", "INR", "BRL", "RUB", 
            "ZAR", "MXN", "TRY", "PLN", "THB", "IDR", "HUF", "CZK", 
            "ILS", "CLP", "PHP", "AED", "COP", "SAR", "MYR", "RON"
        ]
        
        # Криптовалюты для отслеживания
        self.CRYPTO_CURRENCIES = [
            "BTC", "ETH", "BNB", "XRP", "SOL", "DOGE", "ADA", 
            "AVAX", "DOT", "TRX"
        ]
        # API ключи (загружаются из настроек или окружения)
        self.EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")

        # Общие настройки
        self.BASE_CURRENCY = settings.get("DEFAULT_BASE_CURRENCY", "USD")
        self.REQUEST_TIMEOUT = 10
        self.COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
        self.EXCHANGERATE_API_URL = "https://v6.exchangerate-api.com/v6"
        
        
        # Пути к файлам
        self.RATES_FILE_PATH = settings.get('RATES_FILE', 'rates.json')
        self.HISTORY_FILE_PATH = "exchange_rates.json"
    