from datetime import datetime
from typing import Dict, List, Optional

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.database import db

from .api_clients import CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig

config = ParserConfig()


class RatesUpdater:
    """Основной класс для обновления курсов с использованием DatabaseManager"""
    
    def __init__(self, coingecko_client=None, exchangerate_client=None):
        # Принимаем клиенты в конструкторе
        self.coingecko_client = coingecko_client or CoinGeckoClient()
        self.exchangerate_client = exchangerate_client or ExchangeRateApiClient()
        
        # Инициализация файлов через DatabaseManager
        self._init_storage_files()
    
    def _init_storage_files(self):
        """Инициализирует необходимые файлы хранилища"""
        # Инициализируем файл курсов если он пустой
        rates_data = db.load(config.RATES_FILE_PATH)
        if not rates_data:
            default_rates = {
                "pairs": {},
                "last_refresh": datetime.now().isoformat(),
                "source": "initial"
            }
            db.save(config.RATES_FILE_PATH, default_rates)
        
        # Инициализируем файл истории если он пустой
        history_data = db.load(config.HISTORY_FILE_PATH)
        if not isinstance(history_data, list):
            db.save(config.HISTORY_FILE_PATH, [])
    
    def run_update(self, source: Optional[str] = None) -> Dict:
        """Запускает обновление курсов с использованием DatabaseManager"""
        print("Starting rates update...")
        
        all_rates = {}
        sources_used = []
        errors = []
        
        # Опрашиваем CoinGecko
        if source in [None, "coingecko"]:
            try:
                print("Fetching from CoinGecko...", end=" ")
                crypto_rates = self.coingecko_client.fetch_rates()
                all_rates.update(crypto_rates)
                sources_used.append("CoinGecko")
                print(f"OK ({len(crypto_rates)} rates)")
            except ApiRequestError as e:
                errors.append(str(e))
                print(f"ERROR: {str(e)}")
        
        # Опрашиваем ExchangeRate-API
        if source in [None, "exchangerate"]:
            try:
                print("Fetching from ExchangeRate-API...", end=" ")
                fiat_rates = self.exchangerate_client.fetch_rates()
                all_rates.update(fiat_rates)
                sources_used.append("ExchangeRate-API")
                print(f"OK ({len(fiat_rates)} rates)")
            except ApiRequestError as e:
                errors.append(str(e))
                print(f"ERROR: {str(e)}")
        
        if not all_rates:
            raise ApiRequestError("Не удалось получить курсы")
        
        # Формируем данные для сохранения
        cache_data = {
            "pairs": {},
            "last_refresh": datetime.now().isoformat(),
            "source": ", ".join(sources_used) if sources_used else "ParserService"
        }
        
        timestamp = datetime.now().isoformat()
        for pair_key, rate in all_rates.items():
            cache_data["pairs"][pair_key] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": sources_used[0] if sources_used else "ParserService"
            }
        
        # Безопасное сохранение курсов через DatabaseManager
        print(f"Writing {len(all_rates)} rates to {config.RATES_FILE_PATH}...")
        db.save(config.RATES_FILE_PATH, cache_data)
        
        # Сохраняем в историю с использованием DatabaseManager
        self._save_to_history(all_rates, sources_used, timestamp)
        
        # Формируем результат
        result = {
            "success": True,
            "rates_count": len(all_rates),
            "sources": sources_used,
            "errors": errors,
            "last_refresh": cache_data["last_refresh"],
            "file_saved": config.RATES_FILE_PATH
        }
        
        print(f"Update successful. Total rates updated: {len(all_rates)}")
        if errors:
            print(f"Completed with errors: {', '.join(errors)}")
        
        return result
    
    def _save_to_history(self, rates: Dict, sources_used: List[str], timestamp: str):
        """Сохраняет курсы в историю с использованием DatabaseManager"""
        try:
            # Загружаем текущую историю
            history = db.load(config.HISTORY_FILE_PATH)
            
            # Если файл поврежден или не список, создаем новый
            if not isinstance(history, list):
                history = []
                print("Warning: History file was corrupted, creating new one")
            
            # Добавляем новые записи
            for pair_key, rate in rates.items():
                from_currency, to_currency = pair_key.split("_")
                record = {
                    "id": f"{pair_key}_{timestamp}",
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "rate": rate,
                    "timestamp": timestamp,
                    "source": (
                        ", ".join(sources_used) if sources_used else "ParserService"
                    )
                }
                history.append(record)
            
            # Ограничиваем историю последними 1000 записей
            if len(history) > 1000:
                history = history[-1000:]
                print("History truncated to 1000 records")
            
            # Сохраняем историю через DatabaseManager
            db.save(config.HISTORY_FILE_PATH, history)
            
        except Exception as e:
            print(f"Error saving to history: {str(e)}")
    
    def get_current_rates(self) -> Dict:
        """Получить текущие курсы из хранилища"""
        data = db.load(config.RATES_FILE_PATH)
        
        if not data or "pairs" not in data:
            return {}
        
        rates = {}
        for pair_key, pair_data in data["pairs"].items():
            rates[pair_key] = pair_data["rate"]
        
        return rates
    
    def get_rate_history(self, pair_key: Optional[str] = None, 
    limit: int = 100) -> List[Dict]:
        """Получить историю курсов"""
        history = db.load(config.HISTORY_FILE_PATH)
        
        if not isinstance(history, list):
            return []
        
        # Фильтруем по паре если указано
        if pair_key:
            filtered_history = [
                record for record in history 
                if f"{record['from_currency']}_{record['to_currency']}" == pair_key
            ]
        else:
            filtered_history = history
        
        # Ограничиваем количество записей
        return filtered_history[-limit:] if limit else filtered_history
    
    def get_last_update_info(self) -> Dict:
        """Получить информацию о последнем обновлении"""
        data = db.load(config.RATES_FILE_PATH)
        
        if not data:
            return {}
        
        return {
            "last_refresh": data.get("last_refresh"),
            "source": data.get("source", "unknown"),
            "rates_count": len(data.get("pairs", {})),
            "file_path": config.RATES_FILE_PATH
        }
    
    def get_statistics(self) -> Dict:
        """Получить статистику по обновлениям"""
        rates_data = db.load(config.RATES_FILE_PATH)
        history_data = db.load(config.HISTORY_FILE_PATH)
        
        stats = {
            "current_rates_count": len(rates_data.get("pairs", {})) 
                if rates_data else 0,
            "history_records_count": len(history_data) 
                if isinstance(history_data, list) else 0,
            "last_update": rates_data.get("last_refresh") 
                if rates_data else None,
            "update_source": rates_data.get("source") 
                if rates_data else None
}
        
        # Анализ источников в истории
        if isinstance(history_data, list) and history_data:
            sources = {}
            for record in history_data[-100:]:  # Последние 100 записей
                source = record.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            stats["recent_sources"] = sources
        
        return stats


# Функция для удобного использования
def update_rates(source: Optional[str] = None) -> Dict:
    """Удобная функция для обновления курсов"""
    updater = RatesUpdater()
    return updater.run_update(source)


# Функция для получения текущих курсов
def get_current_rates() -> Dict:
    """Получить текущие курсы"""
    updater = RatesUpdater()
    return updater.get_current_rates()