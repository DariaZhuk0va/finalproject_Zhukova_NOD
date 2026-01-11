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
    show_rates,
    show_user_portfolio,
    update_rates,
)
from valutatrade_hub.core.utils import (
    create_portfolio_table,
    create_rate_table,
    create_rates_table,
    create_transaction_table,
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
    
        if result.get("success"):
            data = result.get("data", {})
            table = create_transaction_table(
                "buy",
                data.get("currency", ""),
                data.get("amount", 0),
                data.get("rate", 0),
                data.get("cost_usd", 0),
                data["wallet_before"].get(currency, 0),
                data["wallet_after"].get(currency, 0)
            )
            result["message"] = table
    
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
    
        if result.get("success"):
            data = result.get("data", {})
            table = create_transaction_table(
               "sell",
                data.get("currency", ""),
                data.get("amount", 0),
                data.get("rate", 0),
                data.get("cost_usd", 0),
                data["wallet_before"].get(currency, 0),
                data["wallet_after"].get(currency, 0)
            )
            result["message"] = table
    
        return result
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка при продаже: {str(e)}"
        }


def show_portfolio_command(session_data, base_currency: str = "USD"):
    """Портфель"""
    result = show_user_portfolio(session_data, base_currency)
    if result.get("success"):
        data = result.get("data", {})
        if data == {}:
            return result
        else:
            table = create_portfolio_table(
                data.get("portfolio_items", {}),
                data.get("total", 0),
                data.get("base_currency", "USD"),
                data.get("username", "")
            )
            result["message"] = table
    
            return result
    return result


def get_rate_command(from_currency: str, to_currency: str):
    """Курс с точными сообщениями об ошибках"""
    
    try:
        result = get_exchange_rate(from_currency, to_currency)
    
        if result.get("success"):
            if from_currency == to_currency:
                table = create_rate_table(
                from_currency,
                to_currency,
                1,
                'no update'
                )
            else:
                data = result.get("data", {})
                table = create_rate_table(
                    data.get("from_currency", ""),
                    data.get("to_currency", ""),
                    data.get("rate", 0),
                    data.get("updated_at", "unknown")
                )   
                result["message"] = table
        return result
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
    
def update_rates_command(source=None):
    """Обновить курсы валют"""
    try:
        result = update_rates(source)
        
        if result.get("success"):
            result["message"] = (f"Обновление успешно. Обновлено "
                                 f"{result['rates_count']} курсов")
            
            if result.get('last_refresh'):
                result["message"] += (f" | Последнее обновление: "
                                      f"{result['last_refresh']}")
            
            if result.get('errors'):
                result["message"] += f" | Ошибки: {', '.join(result['errors'])}"
        else:
            result["message"] = (f"Ошибка обновления: "
                                 f"{', '.join(result.get('errors', []))}")
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка обновления курсов: {str(e)}"
        }


def show_rates_command(currency=None, top=None, base="USD"):
    """
    Показать курсы из кеша
    """
    try:
        result = show_rates(currency, top, base)
        
        if result.get("success"):
            data = result.get("data", {})
            table = create_rates_table(
                data.get("table_data", []),
                data.get("last_refresh", "unknown")
            )
            result["message"] = table

        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Ошибка показа курсов: {str(e)}"
        }