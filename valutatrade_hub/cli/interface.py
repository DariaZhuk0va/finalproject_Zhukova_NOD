from datetime import datetime

from valutatrade_hub.core.constants import PORTFOLIOS_FILE, RATES_FILE, USERS_FILE
from valutatrade_hub.core.exceptions import (
    InvalidAmountError,
    InvalidName,
    InvalidPassword,
)
from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.core.utils import is_rate_fresh
from valutatrade_hub.decorators import log_buy, log_login, log_register, log_sell
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import settings


@log_register(verbose=True)
def register_command(username: str, password: str):
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
def login_command(username: str, password: str):
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


def show_portfolio_command(session_data, base_currency: str = "USD"):
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

    # Загрузка курсов валют
    try:
        exchange_rates = db.load(RATES_FILE)
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
            key = f"{currency}_{base_currency}"
            if key in exchange_rates and isinstance(exchange_rates[key], dict):
                rate = exchange_rates[key].get("rate", 0)
                value = balance * rate
            else:
                lines.append(f"- {currency}: {balance:.4f} → НЕТ КУРСА")
                continue

        total += value
        lines.append(f"- {currency}: {balance:.4f} → {value:.2f} {base_currency}")

    lines.append("-" * 40)
    lines.append(f"ИТОГО: {total:,.2f} {base_currency}")

    return {"success": True, "message": "\n".join(lines)}


@log_buy(verbose=True)
def buy_command(session_data, currency: str, amount: float):
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
        return {"success": False, "message": str(InvalidAmountError(amount))}

    # Валидация валюты
    currency = currency.upper().strip()
    if not currency:
        return {"success": False, "message": "Код валюты не может быть пустым"}

    # Получение курса
    rates = db.load(RATES_FILE)
    if currency == "USD":
        rate = 1.0
        base_currency = "USD"
    else:
        rate_key = f"{currency}_USD"

        if rate_key not in rates:
            return {
                "success": False,
                "message": f"Не удалось получить курс для {currency}→USD",
            }

        rate_data = rates[rate_key]
        if not isinstance(rate_data, dict) or "rate" not in rate_data:
            return {
                "success": False,
                "message": f"Не удалось получить курс для {currency}→USD",
            }

        rate = rate_data.get("rate", 0)
        base_currency = "USD"

    if rate <= 0:
        return {
            "success": False,
            "message": f"Не удалось получить курс для {currency}→USD",
        }

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
        return {"success": False, "message": "Портфель не найден"}

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

    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}


@log_sell(verbose=True)
def sell_command(session_data, currency: str, amount: float):
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
        return {"success": False, "message": str(InvalidAmountError(amount))}

    # Валидация валюты
    currency = currency.upper().strip()
    if not currency:
        return {"success": False, "message": "Код валюты не может быть пустым"}

    # Получение курса
    rates = db.load(RATES_FILE)
    # Если продаем USD, то курс всегда 1:1
    if currency == "USD":
        rate = 1.0
        base_currency = "USD"
    else:
        rate_key = f"{currency}_USD"

        if rate_key not in rates:
            return {
                "success": False,
                "message": f"Не удалось получить курс для {currency}→USD",
            }

        rate_data = rates[rate_key]
        if not isinstance(rate_data, dict) or "rate" not in rate_data:
            return {
                "success": False,
                "message": f"Не удалось получить курс для {currency}→USD",
            }

        rate = rate_data.get("rate", 0)
        base_currency = "USD"

    if rate <= 0:
        return {
            "success": False,
            "message": f"Не удалось получить курс для {currency}→USD",
        }

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

    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_rate_command(from_currency: str, to_currency: str):
    """
    Назначение: получить текущий курс одной валюты к другой.
    """
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()

    if not from_currency or not to_currency:
        return {"success": False, "message": "Коды валют не могут быть пустыми"}

    if from_currency == to_currency:
        return {
            "success": True,
            "message": (f"Курс {from_currency}→{to_currency}: "
            "1.0000 (одна и та же валюта)"),
        }

    # Загрузка текущих курсов
    rates = db.load(RATES_FILE)

    key = f"{from_currency}_{to_currency}"
    reverse_key = f"{to_currency}_{from_currency}"

    # Проверяем свежесть курса
    needs_update = False
    rate_data = None
    MAX_AGE_MINUTES = settings.get("RATES_TTL_SECONDS", 300) / 60

    if key in rates:
        rate_data = rates[key]
        if isinstance(rate_data, dict):
            updated_at = rate_data.get("updated_at")
            if not is_rate_fresh(updated_at, MAX_AGE_MINUTES):
                needs_update = True
    elif reverse_key in rates:
        rate_data = rates[reverse_key]
        if isinstance(rate_data, dict):
            updated_at = rate_data.get("updated_at")
            if not is_rate_fresh(updated_at, MAX_AGE_MINUTES):
                needs_update = True
    else:
        needs_update = True

    # Обновляем курс если нужно
    if needs_update:
        print(f"Обновление курса {from_currency}→{to_currency}...")

        # Заглушка для реального API вызова
        if key in rates and isinstance(rates[key], dict):
            rate = rates[key].get("rate")
            updated_at = rates[key].get("updated_at")
        elif reverse_key in rates and isinstance(rates[reverse_key], dict):
            reverse_rate = rates[reverse_key].get("rate")
            rate = 1 / reverse_rate if reverse_rate != 0 else 0
            updated_at = rates[reverse_key].get("updated_at")
        else:
            return {
                "success": False,
                "message": f"Курс {from_currency}→{to_currency} недоступен",
            }
        """
        # Обновляем кеш
        if key not in rates:
            rates[key] = {}
        
        if isinstance(rates[key], dict):
            rates[key]["rate"] = new_rate
            rates[key]["updated_at"] = new_updated_at
        
        # Обновляем last_refresh
        rates["last_refresh"] = datetime.now().isoformat()
        
        # Сохраняем обновленные курсы
        save_json(RATES_FILE, rates)
        
        rate = new_rate
        updated_at = new_updated_at
        source_info = " (только что обновлено)"
"""
    else:
        # Используем существующий курс
        if key in rates and isinstance(rates[key], dict):
            rate = rates[key].get("rate")
            updated_at = rates[key].get("updated_at")
        elif reverse_key in rates and isinstance(rates[reverse_key], dict):
            reverse_rate = rates[reverse_key].get("rate")
            rate = 1 / reverse_rate if reverse_rate != 0 else 0
            updated_at = rates[reverse_key].get("updated_at")
        else:
            return {
                "success": False,
                "message": f"Курс {from_currency}→{to_currency} недоступен",
            }

    # Форматируем результат
    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        time_str = str(updated_at)

    if rate:
        reverse_rate = 1 / rate if rate != 0 else 0
        message = f"Курс {from_currency}→{to_currency}: {rate:.8f}\n"
        message += f"Обновлено: {time_str}\n"
        message += f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.6f}"
        return {"success": True, "message": message}

    return {
        "success": False,
        "message": f"Курс {from_currency}→{to_currency} недоступен",
    }
