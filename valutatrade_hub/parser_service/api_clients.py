import time

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.database import db

from .config import ParserConfig
from .storage import load_rates, save_rates

config = ParserConfig()


class BaseApiClient:
    """Базовый класс для API клиентов"""
    
    def __init__(self, cache_duration=300):  # 5 минут кэша по умолчанию
        self.cache_duration = cache_duration
        self.cache_filename = f"{self.__class__.__name__.lower()}_cache.json"
    
    def fetch_rates(self):
        """Получает курсы валют от API"""
        return {}
    
    def _get_cached_data(self, key="rates"):
        """Получить кэшированные данные"""
        cache_data = load_rates(self.cache_filename)
        
        if key in cache_data:
            cached_item = cache_data[key]
            timestamp = cached_item.get("timestamp", 0)
            data = cached_item.get("data", {})
            
            # Проверяем, не устарели ли кэшированные данные
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _save_to_cache(self, data, key="rates"):
        """Сохранить данные в кэш"""
        cache_data = db.load(self.cache_filename)
        
        cache_data[key] = {
            "timestamp": time.time(),
            "data": data,
            "source": self.__class__.__name__
        }
        
        save_rates(cache_data, self.cache_filename)
    
    def fetch_rates_with_cache(self):
        """Получить курсы с использованием кэша"""
        # Пробуем получить из кэша
        cached_rates = self._get_cached_data()
        if cached_rates is not None:
            print(f"Используем кэшированные данные от {self.__class__.__name__}")
            return cached_rates
        
        # Если нет в кэше или устарело - запрашиваем у API
        print(f"Запрашиваем данные от {self.__class__.__name__}...")
        try:
            rates = self.fetch_rates()
            
            # Сохраняем в кэш если получили данные
            if rates:
                self._save_to_cache(rates)
            
            return rates
        except ApiRequestError as e:
            # В случае ошибки API, пробуем вернуть старые кэшированные данные
            cache_data = db.load(self.cache_filename)
            if "rates" in cache_data:
                print(f"Ошибка API {self.__class__.__name__}, "
                      "используем старые кэшированные данные")
                return cache_data["rates"].get("data", {})
            raise e


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API"""
    
    def fetch_rates(self):
        """Получает курсы криптовалют"""
        # Формируем URL с ids и vs_currencies
        crypto_ids = []
        crypto_codes = []
        
        for code in config.CRYPTO_CURRENCIES:
            if code in config.CRYPTO_ID_MAP:
                crypto_ids.append(config.CRYPTO_ID_MAP[code])
                crypto_codes.append(code)
        
        if not crypto_ids:
            return {}
        
        try:
            # Отправляем GET-запрос
            url = f"{config.COINGECKO_URL}?ids={','.join(crypto_ids)}&vs_currencies=usd"
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            
            # Проверяем статус-код
            if response.status_code != 200:
                raise ApiRequestError(f"HTTP {response.status_code}")
            
            data = response.json()
            
            # Приводим к стандартному формату
            rates = {}
            for code, crypto_id in zip(crypto_codes, crypto_ids):
                if crypto_id in data and "usd" in data[crypto_id]:
                    rate = float(data[crypto_id]["usd"])
                    rates[f"{code}_{config.BASE_CURRENCY}"] = rate
            
            return rates
            
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка сети: {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Ошибка CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API"""
    
    def __init__(self, cache_duration=3600):  # 1 час кэша для фиатных валют
        super().__init__(cache_duration)
    
    def fetch_rates(self):
        """Получает курсы фиатных валют"""
        # Проверяем API ключ
        if not config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("API ключ не установлен")
        
        try:
            # Формируем URL с API-ключом
            url = (f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/"
                   f"latest/{config.BASE_CURRENCY}")
            
            # Отправляем GET-запрос
            response = requests.get(url, timeout=config.REQUEST_TIMEOUT)
            
            # Проверяем статус-код
            if response.status_code != 200:
                raise ApiRequestError(f"HTTP {response.status_code}")
            
            data = response.json()

            # Проверяем успешность API
            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown")
                raise ApiRequestError(f"API ошибка: {error_type}")
            
            # Извлекаем курсы из rates
            api_rates = data.get("conversion_rates", {})

            
            # Приводим к стандартному формату
            rates = {}
            BASE = config.BASE_CURRENCY
            for currency in config.FIAT_CURRENCIES:
                if currency in api_rates:
                    rate_usd_to_currency = api_rates[currency]
                    if rate_usd_to_currency > 0:
                        rate_currency_to_usd = 1 / rate_usd_to_currency
                        rates[f"{currency}_{BASE}"] = rate_currency_to_usd
        
            return rates
            
        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка сети: {str(e)}")
        except Exception as e:
            raise ApiRequestError(f"Ошибка ExchangeRate-API: {str(e)}")


class ApiClientManager:
    """Менеджер для управления всеми API клиентами"""
    
    def __init__(self):
        self.clients = {
            "coingecko": CoinGeckoClient(cache_duration=300),  
            "exchangerate": ExchangeRateApiClient(cache_duration=3600)  
        }
        
        # Файл для хранения истории запросов
        self.history_filename = "api_requests_history.json"
    
    def fetch_all_rates(self, use_cache=True):
        """Получить курсы от всех источников"""
        all_rates = {}
        
        for client_name, client in self.clients.items():
            try:
                if use_cache:
                    rates = client.fetch_rates_with_cache()
                else:
                    rates = client.fetch_rates()
                
                if rates:
                    all_rates.update(rates)
                    
                    # Логируем успешный запрос
                    self._log_request(client_name, success=True)
                else:
                    self._log_request(client_name, success=False, 
                                      error="No data returned")
                    
            except ApiRequestError as e:
                print(f"Ошибка от {client_name}: {str(e)}")
                self._log_request(client_name, success=False, error=str(e))
        
        return all_rates
    
    def _log_request(self, client_name, success=True, error=None):
        """Логировать запросы к API"""
        history = db.load(self.history_filename)
        
        if not isinstance(history, dict):
            history = {"requests": []}
        
        if "requests" not in history:
            history["requests"] = []
        
        log_entry = {
            "timestamp": time.time(),
            "client": client_name,
            "success": success,
            "error": error
        }
        
        history["requests"].append(log_entry)
    
    def get_cache_stats(self):
        """Получить статистику кэша"""
        stats = {}
        
        for client_name, client in self.clients.items():
            cache_data = db.load(client.cache_filename)
            
            if "rates" in cache_data:
                cached_item = cache_data["rates"]
                age = time.time() - cached_item.get("timestamp", 0)
                stats[client_name] = {
                    "age_seconds": age,
                    "age_minutes": age / 60,
                    "data_count": len(cached_item.get("data", {})),
                    "source": cached_item.get("source", "unknown")
                }
        
        return stats


# Глобальный экземпляр менеджера
api_manager = ApiClientManager()