from datetime import datetime
from valutatrade_hub.core.models import (
    User,
    Portfolio,
    Wallet
)
                                         
from valutatrade_hub.core.utils import (
    is_rate_fresh
)
from valutatrade_hub.core.constants import (
    RATES_FILE,
    USERS_FILE,
    PORTFOLIOS_FILE
)
from valutatrade_hub.infra.database import db
from valutatrade_hub.infra.settings import settings

from valutatrade_hub.core.exceptions import (
InvalidAmountError,
InvalidName,
InvalidPassword
)

def register_command(username: str, password: str):
    """
    Регистрация нового пользователя
    
    Args:
        username: Имя пользователя
        password: Пароль
    
    Returns:
        Кортеж (успех, сообщение)
    """
    # 1. Проверка входных данных
    if not username or not username.strip():
        message = InvalidName()
        return False, message
    
    if len(password) < 4:
        message = InvalidPassword()
        return False, message
    
    # 2. Проверка уникальности username
    users = db.load(USERS_FILE)
    
    for user_data in users:
        if user_data.get("username") == username:
            return False, f"Имя пользователя '{username}' уже занято"
    
    # 3. Генерация user_id (автоинкремент)
    if users:
        user_id = max(u.get("user_id", 0) for u in users) + 1
    else:
        user_id = 1
    
    # 4. Создание пользователя с хешированием пароля
    try:
        # Создаем объект User (он сам хеширует пароль)
        user = User(user_id, username, password)
        
        # 5. Сохранение пользователя в users.json
        users.append(user.to_dict())
        db.save(USERS_FILE, users)
        
        # 6. Создание пустого портфеля
        portfolios = db.load(PORTFOLIOS_FILE)
        
        # Проверяем, нет ли уже портфеля для этого пользователя
        portfolio_exists = any(p.get("user_id") == user_id for p in portfolios)
        
        if not portfolio_exists:
            portfolio = Portfolio(user_id)
            portfolios.append(portfolio.to_dict())
            db.save(PORTFOLIOS_FILE, portfolios)
        
        # 7. Возврат сообщения об успехе
        message = (f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                  f"Войдите: login --username {username} --password ****")
        
        return True, message
        
    except Exception as e:
        return False, f"Ошибка при регистрации: {str(e)}"
    
def login_command(username: str, password: str):
    """
    Вход пользователя в систему
    
    Args:
        username: Имя пользователя
        password: Пароль
    
    Returns:
        Кортеж (dict, сообщение)
    """
    # 1. Проверка входных данных
    if not username or not username.strip():
        message = InvalidName()
        return {}, message
    
    if len(password) < 4:
        message = InvalidPassword()
        return {}, message
    
    # 2. Загрузка пользователей
    users = db.load(USERS_FILE)
    
    # 3. Поиск пользователя по username
    user_data = None
    for user in users:
        if user.get("username") == username:
            user_data = user
            break
    
    if not user_data:
        return {}, f"Пользователь '{username}' не найден"
    
    # 4. Проверка пароля
    try:
        # Восстанавливаем пользователя из словаря
        user = User.from_dict(user_data)
        
        # Проверяем пароль
        if not user.verify_password(password):
            return {}, "Неверный пароль"
        
        # 5. Сохранение сессии
        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "login_time": datetime.now().isoformat()
        }
        
        # 6. Возврат сообщения об успехе
        return session_data, f"Вы вошли как '{username}'"
        
    except Exception as e:
        return False, f"Ошибка при входе: {str(e)}"
    
def show_portfolio_command(session_data, base_currency: str = "USD"):
    """
    Показать портфель пользователя
    
    Args:
        base_currency: Базовая валюта конвертации
    
    Returns:
        Кортеж (успех, сообщение)
    """
    # 1. Проверка, что пользователь залогинен
    
    if not session_data:
        return False, "Сначала выполните login"
    
    if base_currency is None:
        base_currency = settings.get('DEFAULT_BASE_CURRENCY', 'USD')
    
    user_id = session_data.get("user_id")
    username = session_data.get("username")
    
    # 2. Загрузка портфеля пользователя
    portfolios = db.load(PORTFOLIOS_FILE)
    
    portfolio_data = None
    for portfolio in portfolios:
        if portfolio.get("user_id") == user_id:
            portfolio_data = portfolio
            break
    
    if not portfolio_data:
        return False, f"Портфель для пользователя '{username}' не найден"
    
    # 3. Проверка наличия кошельков
    wallets = portfolio_data.get("wallets", {})
    
    if not wallets:
        return True, f"Портфель пользователя '{username}' пуст"
    
    # 4. Загрузка курсов валют
    try:
        exchange_rates = db.load(RATES_FILE)
        if not exchange_rates:
            return False, "Курсы валют не загружены"
    except:
        return False, "Ошибка при загрузке курсов валют"
    
    lines = [f"Портфель пользователя '{session_data['username']}' (база: {base_currency}):"]
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
    
    return True, "\n".join(lines)

def buy_command(session_data, currency: str, amount: float):
    """
    Минимальная версия команды покупки
    """
    # 1. Проверка, что пользователь залогинен
    
    if not session_data:
        return False, "Сначала выполните login"
    
    user_id = session_data.get("user_id")
    username = session_data.get("username")
    
    # 2. Валидация суммы
    if not isinstance(amount, (int, float)):
        return False, "'amount' должен быть числом"
    
    if amount <= 0:
        message = InvalidAmountError(amount)
        return False, message
    
    # 3. Валидация валюты
    currency = currency.upper().strip()
    if not currency:
        return False, "Код валюты не может быть пустым"
    
    # 4. Получение курса
    rates = db.load(RATES_FILE)
    rate_key = f"{currency}_USD"
    
    if rate_key not in rates:
        return False, f"Не удалось получить курс для {currency}→USD"
    
    rate_data = rates[rate_key]
    if not isinstance(rate_data, dict) or "rate" not in rate_data:
        return False, f"Не удалось получить курс для {currency}→USD"
    
    rate = rate_data.get("rate", 0)
    if rate <= 0:
        return False, f"Не удалось получить курс для {currency}→USD"
    
    # 5. Расчет стоимости
    cost_usd = amount * rate
    
    # 6. Проверка и обновление портфеля
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
        return False, "Портфель не найден"
    
    portfolio = Portfolio.from_dict(portfolio_data)

    has_wallet = False
    # Сохраняем старые значения
    old_balance = 0
    try:
        old_balance = portfolio.get_wallet(currency).balance
        has_wallet = True
    except:
        old_balance = 0
        has_wallet = False

    
    # Выполняем покупку 
    try:
        
        # Добавляем валюту
        if not has_wallet:
            portfolio.add_currency(currency, amount)
        else:
            wallet = portfolio.get_wallet(currency)
            wallet.deposit(amount)
        
        # 12. Сохраняем
        portfolios[portfolio_idx] = portfolio.to_dict()
        db.save(PORTFOLIOS_FILE, portfolios)
        
        # 13. Формируем отчет
        new_balance = portfolio.get_wallet(currency).balance
        
        return True, (
            f"Покупка выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"  - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
            f"Оценочная стоимость покупки: {cost_usd:,.2f} USD"
        )
    
    except ValueError as e:
        return False, str(e)
    
def sell_command(session_data, currency: str, amount: float):
    """
    Назначение: продать указанную валюту.
    """
    # Проверка, что пользователь залогинен
    
    if not session_data:
        return False, "Сначала выполните login"
    
    user_id = session_data.get("user_id")
    username = session_data.get("username")
    
    # Валидация суммы
    if not isinstance(amount, (int, float)):
        return False, "'amount' должен быть числом"
    
    if amount <= 0:
        message = InvalidAmountError(amount)
        return False, message
    
    # Валидация валюты
    currency = currency.upper().strip()
    if not currency:
        return False, "Код валюты не может быть пустым"
    
    # Получение курса
    rates = db.load(RATES_FILE)
    rate_key = f"{currency}_USD"
    
    if rate_key not in rates:
        return False, f"Не удалось получить курс для {currency}→USD"
    
    rate_data = rates[rate_key]
    if not isinstance(rate_data, dict) or "rate" not in rate_data:
        return False, f"Не удалось получить курс для {currency}→USD"
    
    rate = rate_data.get("rate", 0)
    if rate <= 0:
        return False, f"Не удалось получить курс для {currency}→USD"
    
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
        return False, "Портфель не найден"
    
    portfolio = Portfolio.from_dict(portfolio_data)

    
    # Получаем баланс
    has_wallet = False
    old_balance = 0
    try:
        old_balance = portfolio.get_wallet(currency).balance
        has_wallet = True
    except:
        return False, f'У вас нет кошелька {currency}. Добавьте валюту: она создаётся автоматически при первой покупке'


    # Выполняем продажу 
    try:
        wallet = portfolio.get_wallet(currency)
        wallet.withdraw(amount)
        
        # Сохраняем
        portfolios[portfolio_idx] = portfolio.to_dict()
        db.save(PORTFOLIOS_FILE, portfolios)
        
        # Формируем отчет
        new_balance = portfolio.get_wallet(currency).balance
        
        return True, (
            f"Продажа выполнена: {amount:.4f} {currency} по курсу {rate:.2f} USD/{currency}\n"
            f"Изменения в портфеле:\n"
            f"  - {currency}: было {old_balance:.4f} → стало {new_balance:.4f}\n"
            f"Оценочная выручка: {cost_usd:,.2f} USD"
        )
    
    except ValueError as e:
        return False, str(e)
    
def get_rate_command(from_currency: str, to_currency: str):
    """
    Назначение: получить текущий курс одной валюты к другой.
    """
    from_currency = from_currency.upper().strip()
    to_currency = to_currency.upper().strip()
    
    if not from_currency or not to_currency:
        return False, "Коды валют не могут быть пустыми"
    
    if from_currency == to_currency:
        return True, f"Курс {from_currency}→{to_currency}: 1.0000 (одна и та же валюта)"
    
    # Загрузка текущих курсов
    rates = db.load(RATES_FILE)
    
    key = f"{from_currency}_{to_currency}"
    reverse_key = f"{to_currency}_{from_currency}"
    
    # Проверяем свежесть курса
    needs_update = False
    rate_data = None
    MAX_AGE_MINUTES = settings.get('RATES_TTL_SECONDS', 300) / 60

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
            return False, f"Курс {from_currency}→{to_currency} недоступен"
        '''
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
'''
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
            return False, f"Курс {from_currency}→{to_currency} недоступен"
        
        source_info = ""
    
    # Форматируем результат
    try:
        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        time_str = str(updated_at)
    
    if rate:
        reverse_rate = 1 / rate if rate != 0 else 0
        message = f"Курс {from_currency}→{to_currency}: {rate:.8f}\n"
        message += f"Обновлено: {time_str}\n"
        message += f"Обратный курс {to_currency}→{from_currency}: {reverse_rate:.6f}"
        return True, message
    
    return False, f"Курс {from_currency}→{to_currency} недоступен"