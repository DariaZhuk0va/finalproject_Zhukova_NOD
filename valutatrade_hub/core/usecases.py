from datetime import datetime

from valutatrade_hub.core.constants import PORTFOLIOS_FILE, RATES_FILE, USERS_FILE
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
    InvalidName,
    InvalidPassword,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import convert_rates
from valutatrade_hub.decorators import log_buy, log_login, log_register, log_sell
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import settings
from valutatrade_hub.parser_service.updater import RatesUpdater


@log_register(verbose=True)
def register_user(username: str, password: str):
    """
    Регистрация нового пользователя

    Args:
        username: Имя пользователя
        password: Пароль

    Returns:
        Кортеж (успех, сообщение)
    """
    # Проверка входных данных
    if not username or not username.strip():
        message = InvalidName()
        return {"success": False, "message": message}

    if len(password) < 4:
        message = InvalidPassword()
        return {"success": False, "message": message}

    # Проверка уникальности username
    users = db.load(USERS_FILE)

    for user_data in users:
        if user_data.get("username") == username:
            return {
                "success": False,
                "message": f"Имя пользователя '{username}' уже занято",
            }

    # Генерация user_id (автоинкремент)
    if users:
        user_id = max(u.get("user_id", 0) for u in users) + 1
    else:
        user_id = 1

    # Создание пользователя с хешированием пароля
    try:
        user = User(user_id, username, password)
        users.append(user.to_dict())
        db.save(USERS_FILE, users)
        portfolios = db.load(PORTFOLIOS_FILE)
        portfolio_exists = any(p.get("user_id") == user_id for p in portfolios)

        if not portfolio_exists:
            portfolio = Portfolio(user_id)
            portfolios.append(portfolio.to_dict())
            db.save(PORTFOLIOS_FILE, portfolios)

        # Возврат сообщения об успехе
        message = (
            f"Пользователь '{username}' зарегистрирован (id={user_id}). "
            f"Войдите: login --username {username} --password ****"
        )

        return {
            "success": True,
            "message": message,
            "data": {"user_id": user_id, "username": username},
        }

    except Exception as e:
        return {"success": False, "message": f"Ошибка при регистрации: {str(e)}"}


@log_login(verbose=True)
def login_user(username: str, password: str):
    """
    Вход пользователя в систему

    Args:
        username: Имя пользователя
        password: Пароль

    Returns:
        Кортеж (dict, сообщение)
    """
    # Проверка входных данных
    if not username or not username.strip():
        message = InvalidName()
        return {"success": False, "message": message}

    if len(password) < 4:
        message = InvalidPassword()
        return {"success": False, "message": message}

    # Загрузка пользователей
    users = db.load(USERS_FILE)

    # Поиск пользователя по username
    user_data = None
    for user in users:
        if user.get("username") == username:
            user_data = user
            break

    if not user_data:
        return {"success": False, "message": f"Пользователь '{username}' не найден"}

    # Проверка пароля
    try:

        user = User.from_dict(user_data)
        if not user.verify_password(password):
            return {"success": False, "message": "Неверный пароль"}

        # Сохранение сессии
        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "login_time": datetime.now().isoformat(),
        }

        # Возврат сообщения об успехе
        return {
            "success": True,
            "message": f"Вы вошли как '{username}'",
            "data": session_data,
        }

    except Exception as e:
        return {"success": False, "message": f"Ошибка при входе: {str(e)}"}


def show_user_portfolio(session_data, base_currency: str = "USD"):
    """
    Показать портфель пользователя

    Args:
        base_currency: Базовая валюта конвертации

    Returns:
        Кортеж (успех, сообщение)
    """
    # Проверка, что пользователь залогинен
    if not session_data:
        return {"success": False, "message": "Сначала выполните login"}

    if base_currency is None:
        base_currency = settings.get("DEFAULT_BASE_CURRENCY", "USD")

    user_id = session_data.get("user_id")
    username = session_data.get("username")

    # Загрузка портфеля пользователя
    portfolios = db.load(PORTFOLIOS_FILE)

    portfolio_data = None
    for portfolio in portfolios:
        if portfolio.get("user_id") == user_id:
            portfolio_data = portfolio
            break

    if not portfolio_data:
        return {
            "success": False,
            "message": f"Портфель для пользователя '{username}' не найден",
        }

    # Проверка наличия кошельков
    wallets = portfolio_data.get("wallets", {})

    if not wallets:
        return {"success": True, "message": f"Портфель пользователя '{username}' пуст"}

    try:
        exchange_rates_data = db.load(RATES_FILE)
        
        # Извлекаем курсы 
        exchange_rates = {}
        if isinstance(exchange_rates_data, dict):
            if "pairs" in exchange_rates_data:
                pairs = exchange_rates_data.get("pairs", {})
                for pair_key, pair_data in pairs.items():
                    if isinstance(pair_data, dict):
                        exchange_rates[pair_key] = pair_data.get("rate", 0)
                    else:
                        exchange_rates[pair_key] = pair_data
            else:
                exchange_rates = exchange_rates_data
        
        if not exchange_rates:
            return {"success": False, "message": "Курсы валют не загружены"}
            
    except Exception:
        return {"success": False, "message": "Ошибка при загрузке курсов валют"}
    
    lines = [
        f"Портфель пользователя '{session_data['username']}' (база: {base_currency}):"
    ]
    total = 0

    for currency, wallet in wallets.items():
        balance = wallet["balance"]

        if currency == base_currency:
            value = balance
        else:
            result = convert_rates(currency, base_currency, exchange_rates)
            rate = result['result']
            message = result['message']
            if rate == 0:
                return message
            else:
                value = balance * rate

        total += value
        lines.append(f"- {currency}: {balance:.4f} → {value:.2f} {base_currency}")

    lines.append("-" * 40)
    lines.append(f"ИТОГО: {total:,.2f} {base_currency}")

    return {"success": True, "message": "\n".join(lines)}


@log_buy(verbose=True)
def buy_currency(session_data, currency: str, amount: float):
    """
    Минимальная версия команды покупки
    """
    # Проверка, что пользователь залогинен

    if not session_data:
        return {"success": False, "message": "Сначала выполните login"}

    user_id = session_data.get("user_id")

    # Валидация суммы
    if not isinstance(amount, (int, float)):
        return {"success": False, "message": "'amount' должен быть числом"}

    if amount <= 0:
        raise InvalidAmountError(amount)

    # Валидация валюты
    currency_obj = get_currency(currency)  
    currency_code = currency_obj.code

    # Получение курса
    rates_data = db.load(RATES_FILE)
    
    # Извлекаем курсы из нового формата
    rates = {}
    if isinstance(rates_data, dict):
        if "pairs" in rates_data:
            pairs = rates_data.get("pairs", {})
            for pair_key, pair_data in pairs.items():
                rates[pair_key] = pair_data 
    else:
        rates = rates_data
    
    if currency_code == "USD":
        rate = 1.0
        base_currency = "USD"
    else:
        rate_key = f"{currency_code}_USD"

        if rate_key not in rates:
            raise ApiRequestError(f"Курс для {currency_code}→USD не найден")

        rate_data = rates[rate_key]
        if not isinstance(rate_data, dict) or "rate" not in rate_data:
            raise ApiRequestError(f"Неверный формат курса для {currency_code}")

        rate = rate_data.get("rate", 0)
        base_currency = "USD"

    if rate <= 0:
        raise ApiRequestError(f"Некорректный курс для {currency_code}: {rate}")

    # Расчет стоимости
    cost_usd = amount * rate

    # Проверка и обновление портфеля
    portfolios = db.load(PORTFOLIOS_FILE)
    portfolio_data = None
    portfolio_idx = -1

    for i, p in enumerate(portfolios):
        if p["user_id"] == user_id:
            portfolio_data = p
            portfolio_idx = i
            break

    if not portfolio_data:
        portfolio = Portfolio(user_id)
        portfolios.append(portfolio.to_dict())
        db.save(PORTFOLIOS_FILE, portfolios)

    portfolio = Portfolio.from_dict(portfolio_data)

    has_wallet = False

    # Сохраняем старые значения
    old_balance = 0
    try:
        old_balance = portfolio.get_wallet(currency).balance
        has_wallet = True
    except Exception:
        old_balance = 0
        has_wallet = False

    # Сохраняем состояние кошелька до операции
    wallet_before = {}
    for curr, wallet in portfolio.wallets.items():
        wallet_before[curr] = wallet.balance

    # Выполняем покупку
    try:

        # Добавляем валюту
        if not has_wallet:
            portfolio.add_currency(currency, amount)
        else:
            wallet = portfolio.get_wallet(currency)
            wallet.deposit(amount)

        # Сохраняем
        portfolios[portfolio_idx] = portfolio.to_dict()
        db.save(PORTFOLIOS_FILE, portfolios)

        # Сохраняем состояние кошелька после операции
        wallet_after = {}
        for curr, wallet in portfolio.wallets.items():
            wallet_after[curr] = wallet.balance

        # Формируем отчет
        new_balance = portfolio.get_wallet(currency).balance
        message = (
            f"Покупка выполнена: {amount:.4f} {currency} "
            f"по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"  - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
            f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
        )

        return {
            "success": True,
            "message": message,
            "data": {
                "rate": rate,
                "base": base_currency,
                "currency": currency,
                "amount": amount,
                "cost_usd": cost_usd,
                "wallet_before": wallet_before,
                "wallet_after": wallet_after,
            },
        }

    except (InvalidAmountError,
            CurrencyNotFoundError,
            ApiRequestError,
            ValueError) as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Ошибка при покупке: {str(e)}"}


@log_sell(verbose=True)
def sell_currency(session_data, currency: str, amount: float):
    """
    Назначение: продать указанную валюту.
    """
    # Проверка, что пользователь залогинен

    if not session_data:
        return {"success": False, "message": "Сначала выполните login"}

    user_id = session_data.get("user_id")

    # Валидация суммы
    if not isinstance(amount, (int, float)):
        return {"success": False, "message": "'amount' должен быть числом"}

    if amount <= 0:
        raise InvalidAmountError(amount)

    # Валидация валюты
    currency_obj = get_currency(currency)  
    currency_code = currency_obj.code
    
    # Получение курса
    rates_data = db.load(RATES_FILE)
    
    # Извлекаем курсы из нового формата
    rates = {}
    if isinstance(rates_data, dict):
        if "pairs" in rates_data:
            pairs = rates_data.get("pairs", {})
            for pair_key, pair_data in pairs.items():
                rates[pair_key] = pair_data 
        else:
            rates = rates_data
    
    # Если продаем USD, то курс всегда 1:1
    if currency_code == "USD":
        rate = 1.0
        base_currency = "USD"
    else:
        rate_key = f"{currency_code}_USD"

        if rate_key not in rates:
            raise ApiRequestError(f"Курс для {currency_code}→USD не найден")

        rate_data = rates[rate_key]
        if not isinstance(rate_data, dict) or "rate" not in rate_data:
            raise ApiRequestError(f"Неверный формат курса для {currency_code}")

        rate = rate_data.get("rate", 0)
        base_currency = "USD"

    if rate <= 0:
        raise ApiRequestError(f"Некорректный курс для {currency_code}: {rate}")

    # Расчет стоимости
    cost_usd = amount * rate

    # Проверка и обновление портфеля
    portfolios = db.load(PORTFOLIOS_FILE)

    # Ищем портфель пользователя
    portfolio_data = None
    portfolio_idx = -1
    for i, p in enumerate(portfolios):
        if p["user_id"] == user_id:
            portfolio_data = p
            portfolio_idx = i
            break

    if not portfolio_data:
        return {"success": False, "message": "Портфель не найден"}

    portfolio = Portfolio.from_dict(portfolio_data)

    # Получаем баланс
    old_balance = 0
    try:
        old_balance = portfolio.get_wallet(currency).balance
    except Exception:
        return {
        "success": False,
        "message": (
            f"У вас нет кошелька {currency}. "
            "Добавьте валюту: она создаётся автоматически при первой покупке"
        ),
}

    # Сохраняем состояние кошелька до операции
    wallet_before = {}
    for curr, wallet in portfolio.wallets.items():
        wallet_before[curr] = wallet.balance

    # Выполняем продажу
    try:
        wallet = portfolio.get_wallet(currency)
        wallet.withdraw(amount)

        # Сохраняем
        portfolios[portfolio_idx] = portfolio.to_dict()
        db.save(PORTFOLIOS_FILE, portfolios)

        # Сохраняем состояние кошелька после операции
        wallet_after = {}
        for curr, wallet in portfolio.wallets.items():
            wallet_after[curr] = wallet.balance

        # Формируем отчет
        new_balance = portfolio.get_wallet(currency).balance

        message = (
            f"Продажа выполнена: {amount:.4f} {currency} "
            f"по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"  - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
            f"Оценочная выручка: {cost_usd:,.2f} USD"
        )

        return {
            "success": True,
            "message": message,
            "data": {
                "rate": rate,
                "base": base_currency,
                "currency": currency,
                "amount": amount,
                "cost_usd": cost_usd,
                "wallet_before": wallet_before,
                "wallet_after": wallet_after,
            },
        }

    except (InvalidAmountError, CurrencyNotFoundError, 
            ApiRequestError, InsufficientFundsError, ValueError) as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Ошибка при продаже: {str(e)}"}


def get_exchange_rate(from_currency: str, to_currency: str):
    """
    Назначение: получить текущий курс одной валюты к другой.
    """
    try:
        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if not from_currency or not to_currency:
            raise ValueError("Коды валют не могут быть пустыми")
        if from_currency == to_currency:
            return {
                "success": True,
                "message": (f"Курс {from_currency}→{to_currency}: "
                "1.0000 (одна и та же валюта)"),
            }

        # Валидация валют
        from_currency_obj = get_currency(from_currency)
        to_currency_obj = get_currency(to_currency)

        from_code = from_currency_obj.code
        to_code = to_currency_obj.code

        # Загрузка текущих курсов
        rates_data = db.load(RATES_FILE)
        last_refresh = rates_data.get("last_refresh")
    
        if last_refresh != "unknown":
            try:
                dt = datetime.fromisoformat(last_refresh.replace("Z", "+00:00"))
                now = datetime.now()
                time_diff = (now - dt).total_seconds()
            
                if time_diff > settings.get("RATES_TTL_SECONDS", 300):
                    try:
                        from valutatrade_hub.parser_service.updater import RatesUpdater
                        updater = RatesUpdater()
                        result = updater.run_update()
                        if result.get("success"):
                            rates_data = db.load(RATES_FILE)  
                    except Exception as update_error:
                        pass
            except Exception as time_error:
                pass

        # Извлекаем курсы из нового формата
        rates = {}
        if isinstance(rates_data, dict):
            if "pairs" in rates_data:
                # Новый формат: {"pairs": {"BTC_USD": {"rate": ..., ...}, ...}}
                pairs = rates_data.get("pairs", {})
                for pair_key, pair_data in pairs.items():
                    if isinstance(pair_data, dict):
                        rates[pair_key] = pair_data.get("rate", 0)
                    else:
                        rates[pair_key] = pair_data
            else:
                # Старый формат: {"BTC_USD": 59337.21, ...}
                rates = rates_data

        BASE = settings.get("DEFAULT_BASE_CURRENCY", 'USD')
        
        # Проверяем наличие курсов
        direct_key = f"{from_code}_{to_code}"
        reverse_key = f"{to_code}_{from_code}"
        base_key_from = f"{from_code}_{BASE}"
        base_key_to = f"{to_code}_{BASE}"
        
        rate = None
        updated_at = "unknown"
        
        # 1. Проверяем прямой курс
        if direct_key in rates:
            rate = rates[direct_key]
            # Получаем время обновления если есть
            if isinstance(rates_data, dict) and "pairs" in rates_data:
                pair_data = rates_data["pairs"].get(direct_key, {})
                if isinstance(pair_data, dict):
                    updated_at = pair_data.get("updated_at", "unknown")
        
        # 2. Проверяем обратный курс
        elif reverse_key in rates:
            reverse_rate = rates[reverse_key]
            if reverse_rate != 0:
                rate = 1 / reverse_rate
                # Получаем время обновления если есть
                if isinstance(rates_data, dict) and "pairs" in rates_data:
                    pair_data = rates_data["pairs"].get(reverse_key, {})
                    if isinstance(pair_data, dict):
                        updated_at = pair_data.get("updated_at", "unknown")
        
        # 3. Пытаемся через базовую валюту (USD)
        elif base_key_from in rates and base_key_to in rates:
            rate_from = rates[base_key_from]
            rate_to = rates[base_key_to]
            if rate_to != 0:
                rate = rate_from / rate_to
                # Берем самое свежее время обновления
                if isinstance(rates_data, dict) and "pairs" in rates_data:
                    pair_data_from = rates_data["pairs"].get(base_key_from, {})
                    if isinstance(pair_data_from, dict):
                        updated_at = pair_data_from.get("updated_at", "unknown")
        
        if rate is None or rate == 0:
            raise ApiRequestError(f"Курс {from_code}→{to_code} недоступен")
        
        # Если время обновления неизвестно, берем общее время
        if updated_at == "unknown" and isinstance(rates_data, dict):
            updated_at = rates_data.get("last_refresh", "unknown")
        
        # Форматируем результат
        reverse_rate = 1 / rate if rate != 0 else 0
        
        # Форматируем время
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            time_str = str(updated_at)
        
        message = f"Курс {from_code}→{to_code}: {rate:.8f}\n"
        message += f"Обновлено: {time_str}\n"
        message += f"Обратный курс {to_code}→{from_code}: {reverse_rate:.6f}"
        
        return {"success": True, "message": message}
    
    except (ValueError, CurrencyNotFoundError, ApiRequestError) as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Ошибка при получении курса: {str(e)}"}
    
def update_rates(source=None):
    """Use case для обновления курсов валют"""
    try:
        print("Starting rates update...")
        
        updater = RatesUpdater()
        result = updater.run_update(source=source)
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "errors": [str(e)]
        }


def show_rates(currency=None, top=None, base="USD"):
    """Use case для показа курсов из кеша"""
    try:
        if currency != None:
            currency_obj = get_currency(currency)
            currency = currency_obj.code
        
        if base != None:
            base_obj = get_currency(base)
            base = base_obj.code
        
        rates_data = db.load(RATES_FILE)
        
        if not rates_data or "pairs" not in rates_data:
            return {
                "success": False,
                "message": ("Локальный кеш курсов пуст. Выполните 'update-rates', "
                "чтобы загрузить данные."),
                "rates": []
            }
        
        pairs = rates_data.get("pairs", {})
        last_refresh = rates_data.get("last_refresh", "unknown")
        BASE = settings.get("DEFAULT_BASE_CURRENCY", 'USD')

        # Фильтрация по валюте
        filtered_rates = {}
        if currency == BASE or currency == None:
            filtered_rates[f'{BASE}_{BASE}'] = 1
        if currency:
            currency = currency.upper()
            for pair_key, pair_data in pairs.items():
                if currency in pair_key:
                    if isinstance(pair_data, dict):
                        filtered_rates[pair_key] = pair_data.get("rate", 0)
                    else:
                        filtered_rates[pair_key] = pair_data
            
            if not filtered_rates:
                return {
                    "success": False,
                    "message": f"Курс для '{currency}' не найден в кеше.",
                    "rates": []
                }
        else:
            for pair_key, pair_data in pairs.items():
                if isinstance(pair_data, dict):
                    filtered_rates[pair_key] = pair_data.get("rate", 0)
                else:
                    filtered_rates[pair_key] = pair_data
        
        if base != BASE:
            filtered_rates_copy = filtered_rates.copy()
            filtered_rates = {}
            for pair_key, pair_data in filtered_rates_copy.items():
                from_currency, to_currency = pair_key.split("_")
                result = convert_rates(base, from_currency, rates_data)
                key_base = f'{from_currency}_{base}'
                base_rate = result['result']
                if base_rate == 0:
                    return {
                        "success": False,
                        "message": result['message'],
                        "rates": []
                    }
                else:
                    filtered_rates[key_base] = base_rate



        # Сортировка
        sorted_rates = sorted(filtered_rates.items(), key=lambda x: x[1], reverse=True)
        
        # Ограничение топом
        if top:
            sorted_rates = sorted_rates[:top]
        
        # Форматирование результата
        rates_list = []
        for pair_key, rate in sorted_rates:
            rates_list.append({
                "pair": pair_key,
                "rate": rate
            })
        
        return {
            "success": True,
            "rates": rates_list,
            "count": len(rates_list),
            "last_refresh": last_refresh,
            "message": f"Найдено {len(rates_list)} курсов в кеше"
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "rates": []
        }

