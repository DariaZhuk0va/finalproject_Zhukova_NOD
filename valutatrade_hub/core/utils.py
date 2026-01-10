import json
import os
from datetime import datetime, timedelta

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
        print("Папка data создана")
    
    # Файлы и их содержимое по умолчанию
    files_config = {
        USERS_FILE: [],
        PORTFOLIOS_FILE: [],
        RATES_FILE: {
            "EUR_USD": {"rate": 1.0786, "updated_at": "2025-10-09T10:30:00"},
            "BTC_USD": {"rate": 59337.21, "updated_at": "2025-10-09T10:29:42"},
            "RUB_USD": {"rate": 0.01016, "updated_at": "2025-10-09T10:31:12"},
            "ETH_USD": {"rate": 3720.00, "updated_at": "2025-10-09T10:35:00"},
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
                print(f"Файл {filename} создан")
            except Exception as e:
                print(f"Ошибка создания {filename}: {e}")
        else:
            print(f"Файл {filename} уже существует")


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

    exchange_rates = rates

    if to_key == f"{BASE}_{BASE}":
        rate_base = 1
    elif to_key in exchange_rates and isinstance(exchange_rates[to_key], dict):
        rate_base = exchange_rates[to_key].get("rate", 0)
    else:
        return {"result": 0, "message": f"Курс для {to_key}→USD не найден"}
      
    if from_key == f"{BASE}_{BASE}":
        rate_curr = 1
        rate = rate_curr / rate_base
    elif from_key in exchange_rates and isinstance(exchange_rates[from_key], dict):
        rate_curr = exchange_rates[from_key].get("rate", 0)
        rate = rate_curr / rate_base
    else:
        return {"result": 0, "message": f"Курс для {from_key}→{to_key} не найден"}
    
    return {"result": rate, "message": "Успешно"}