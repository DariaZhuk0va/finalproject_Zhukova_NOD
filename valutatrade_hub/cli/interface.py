from datetime import datetime
from models import User, Portfolio
from utils import load_json, save_json

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
    users = load_json("users.json")
    
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
        save_json("users.json", users)
        
        # 6. Создание пустого портфеля
        portfolios = load_json("portfolios.json")
        
        # Проверяем, нет ли уже портфеля для этого пользователя
        portfolio_exists = any(p.get("user_id") == user_id for p in portfolios)
        
        if not portfolio_exists:
            portfolio = Portfolio(user_id)
            portfolios.append(portfolio.to_dict())
            save_json("portfolios.json", portfolios)
        
        # 7. Возврат сообщения об успехе
        message = (f"Пользователь '{username}' зарегистрирован (id={user_id}). "
                  f"Войдите: login --username {username} --password ****")
        
        return True, message
        
    except Exception as e:
        return False, f"Ошибка при регистрации: {str(e)}"