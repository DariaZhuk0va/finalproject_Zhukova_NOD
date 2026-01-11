import json
import os
from datetime import datetime, timedelta

from prettytable import PrettyTable

from valutatrade_hub.core.constants import (
    DATA_DIR,
    PORTFOLIOS_FILE,
    RATES_FILE,
    USERS_FILE,
)
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.infra.settings import settings


def initialize_files():
    """Создает необходимые файлы если их нет"""
    
    # Создаем папку data если её нет
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    # Файлы и их содержимое по умолчанию
    files_config = {
        USERS_FILE: [],
        PORTFOLIOS_FILE: [],
        RATES_FILE: {
            "pairs": {
                "EUR_USD": {
                    "rate": 1.0786, 
                    "updated_at": "2025-10-09T10:30:00", 
                    "source": "ParserService"
                    },
                "BTC_USD": {
                    "rate": 59337.21, 
                    "updated_at": "2025-10-09T10:29:42", 
                    "source": "ParserService"
                    },
                "RUB_USD": {"rate": 0.01016, 
                            "updated_at": "2025-10-09T10:31:12", 
                            "source": "ParserService"
                            },
                "ETH_USD": {"rate": 3720.00, 
                            "updated_at": "2025-10-09T10:35:00", 
                            "source": "ParserService"
                            }
            },
            "source": "ParserService",
            "last_refresh": "2025-10-09T10:35:00"
        }
    }
    
    for filename, default_content in files_config.items():
        filepath = os.path.join(DATA_DIR, filename)
        
        if not os.path.exists(filepath):
            try:
                # Создаем файл с содержимым по умолчанию
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(default_content, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Ошибка создания {filename}: {e}")
        else:
            pass
            


def is_rate_fresh(updated_at: str, max_age_minutes: int = 5) -> bool:
    """
    Проверяет, свежий ли курс (не старше max_age_minutes минут)

    Args:
        updated_at: Время обновления курса в формате ISO строки
                   (например: "2025-10-09T10:30:00")
        max_age_minutes: Максимальный допустимый возраст в минутах (по умолчанию 5)

    Returns:
        True если курс свежий (моложе max_age_minutes минут)
        False если курс устарел или время невалидное
    """
    if not updated_at:
        return False

    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        age = datetime.now() - dt
        return age < timedelta(minutes=max_age_minutes)

    except (ValueError, TypeError):
        return False


def print_help():
    """Показывает справку по командам системы управления портфелем."""

    print("\n***Система управления портфелем валют***")

    print("\n***Регистрация и авторизация***")
    print(
        "register --username <имя> --password <пароль> - "
        "регистрация пользователя, пароль должен быть не менее 4-х символов"
    )
    print("login --username <имя> --password <пароль> - вход в систему")
    print("logout - выход из системы")

    print("\n***Управление портфелем***")
    print("show-portfolio [--base <валюта>] - показать портфель (по умолчанию USD)")
    print("buy --currency <валюта> --amount <количество> - купить валюту")
    print("sell --currency <валюта> --amount <количество> - продать валюту")

    print("\n***Информация о курсах***")
    print("get-rate --from <валюта> --to <валюта> - получить курс валют")

    print("\n***Парсер курсов валют***")
    print("update-rates [--source <coingecko|exchangerate>] - обновить курсы валют")
    print("show-rates [--currency <валюта>] [--top <число>] [--base <валюта>] "
          "- показать курсы из кеша")

    print("\n***Общие команды***")
    print("help - показать эту справку")
    print("exit - выход из программы\n")

def convert_rates(from_currency, to_currency, rates):
    BASE = settings.get("DEFAULT_BASE_CURRENCY", 'USD')
    
    from_currency_obj = get_currency(from_currency)
    to_currency_obj = get_currency(to_currency)

    from_code = from_currency_obj.code
    to_code = to_currency_obj.code

    from_key = f"{from_code}_{BASE}"
    to_key = f"{to_code}_{BASE}"

    exchange_rates = {}
    if isinstance(rates, dict):
        if "pairs" in rates:
            pairs = rates.get("pairs", {})
            for pair_key, pair_data in pairs.items():
                if isinstance(pair_data, dict):
                    exchange_rates[pair_key] = pair_data.get("rate", 0)
                else:
                    exchange_rates[pair_key] = pair_data
        else:
            exchange_rates = rates
    else:
        exchange_rates = rates or {}
    if to_key == f"{BASE}_{BASE}":
        rate_base = 1
    elif to_key in exchange_rates:
        rate_base = exchange_rates.get(to_key, 0)
    else:
        return {"result": 0, "message": f"Курс для {from_code}→USD не найден"}
      
    if from_key == f"{BASE}_{BASE}":
        rate_curr = 1
        rate = rate_curr / rate_base
    elif from_key in exchange_rates:
        rate_curr = exchange_rates.get(from_key, 0)
        rate = rate_curr / rate_base
    else:
        return {"result": 0, "message": f"Курс для {from_code}→{to_code} не найден"}
    
    return {"result": rate, "message": "Успешно"}

def create_portfolio_table(wallets_data, total, base, username):
    """Создает таблицу портфеля (возвращает строку)"""
    table = PrettyTable()
    table.field_names = ["Валюта", "Баланс", f"В {base}"]
    
    for wallet in wallets_data:
        currency = wallet['currency']
        balance = wallet['balance']
        value = wallet['value']
        table.add_row([currency, f"{balance:.4f}", f"{value:.2f}"])
    
    table.add_row(["", "", ""])
    table.add_row(["ИТОГО", "", f"{total:.2f} {base}"])
    
    return str(table)

def create_rates_table(rates_list, last_refresh):
    """Создает таблицу курсов (возвращает строку)"""
    if not rates_list:
        return "Нет данных"
    
    table = PrettyTable()
    table.field_names = ["Пара", "Курс"]
    
    for rate in rates_list:
        try:
            rate_converted = rate['rate']
            rate_converted = float(rate_converted)
        except Exception:
            raise ValueError ('Неверный формат')
        table.add_row([rate['pair'], f"{rate_converted:.6f}"])
    
    return f"Курсы ({last_refresh}):\n{table}"

def create_rate_table(from_curr, to_curr, rate, updated_at):
    """Таблица одного курса"""
    table = PrettyTable()
    try:
        rate = float(rate)
    except Exception:
        raise ValueError ('Неверный формат')
    table.field_names = ["Параметр", "Значение"]
    
    table.add_row(["Пара", f"{from_curr} → {to_curr}"])
    table.add_row(["Курс", f"{rate:.8f}"])
    table.add_row(["Обратный", f"{1/rate:.8f}" if rate != 0 else "0"])
    table.add_row(["Обновлено", updated_at])
    
    return str(table)

def create_transaction_table(op_type, currency, amount, rate, cost, old_bal, new_bal):
    """Таблица транзакции"""
    table = PrettyTable()
    table.field_names = ["Параметр", "Значение"]
    
    op_name = "ПОКУПКА" if op_type == "buy" else "ПРОДАЖА"
    cost_name = "Стоимость" if op_type == "buy" else "Выручка"
    
    table.add_row(["Операция", op_name])
    table.add_row(["Валюта", currency])
    table.add_row(["Количество", f"{amount:.4f}"])
    table.add_row(["Курс USD", f"{rate:.2f}"])
    table.add_row([cost_name, f"{cost:.2f} USD"])
    table.add_row(["Было", f"{old_bal:.4f}"])
    table.add_row(["Стало", f"{new_bal:.4f}"])
    
    return str(table)