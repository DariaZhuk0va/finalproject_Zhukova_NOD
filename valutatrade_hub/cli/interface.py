from datetime import datetime
from valutatrade_hub.core.models import User, Portfolio
from valutatrade_hub.core.utils import load_json, save_json
from valutatrade_hub.core.constants import (
    RATES_FILE,
    USERS_FILE,
    PORTFOLIOS_FILE
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
        return False, "Имя пользователя не может быть пустым"
    
    if len(password) < 4:
        return False, "Пароль должен быть не короче 4 символов"
    
    # 2. Проверка уникальности username
    users = load_json(USERS_FILE)
    
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
        save_json(USERS_FILE, users)
        
        # 6. Создание пустого портфеля
        portfolios = load_json(PORTFOLIOS_FILE)
        
        # Проверяем, нет ли уже портфеля для этого пользователя
        portfolio_exists = any(p.get("user_id") == user_id for p in portfolios)
        
        if not portfolio_exists:
            portfolio = Portfolio(user_id)
            portfolios.append(portfolio.to_dict())
            save_json(PORTFOLIOS_FILE, portfolios)
        
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
        return {}, "Имя пользователя не может быть пустым"
    
    if len(password) < 4:
        return {}, "Пароль должен быть не короче 4 символов"
    
    # 2. Загрузка пользователей
    users = load_json(USERS_FILE)
    
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
    
    user_id = session_data.get("user_id")
    username = session_data.get("username")
    
    # 2. Загрузка портфеля пользователя
    portfolios = load_json(PORTFOLIOS_FILE)
    
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
        exchange_rates = load_json(RATES_FILE)
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