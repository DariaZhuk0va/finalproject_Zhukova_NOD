"""
CLI интерфейс - простые обертки с улучшенными сообщениями
"""
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_exchange_rate,
    login_user,
    register_user,
    sell_currency,
    show_user_portfolio,
)


def register_command(username: str, password: str):
    """Регистрация"""
    return register_user(username, password)


def login_command(username: str, password: str):
    """Вход"""
    return login_user(username, password)


def buy_command(session_data, currency: str, amount: float):
    """Покупка с улучшенными сообщениями"""
    try:
        result = buy_currency(session_data, currency, amount)
        if result["success"]:
            # Добавляем префикс для успешной операции
            result["message"] = "Успешно! " + result["message"]
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при покупке: {str(e)}"
        }


def sell_command(session_data, currency: str, amount: float):
    """Продажа с улучшенными сообщениями"""
    try:
        result = sell_currency(session_data, currency, amount)
        if result["success"]:
            # Добавляем префикс для успешной операции
            result["message"] = "Успешно! " + result["message"]
        return result
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при продаже: {str(e)}"
        }


def show_portfolio_command(session_data, base_currency: str = "USD"):
    """Портфель"""
    return show_user_portfolio(session_data, base_currency)


def get_rate_command(from_currency: str, to_currency: str):
    """Курс с точными сообщениями об ошибках"""
    
    try:
        return get_exchange_rate(from_currency, to_currency)
    except CurrencyNotFoundError as e:
        return {
            "success": False,
            "message": f"Ошибка: валюта не найдена. {str(e)}"
        }
    except ApiRequestError as e:
        return {
            "success": False,
            "message": f"Ошибка получения курса: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }