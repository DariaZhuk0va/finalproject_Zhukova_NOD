from datetime import datetime
from datetime import timedelta


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
        # 1. Преобразуем строку времени в объект datetime
        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        
        # 2. Вычисляем возраст курса (разницу между текущим временем и временем обновления)
        age = datetime.now() - dt
        
        # 3. Проверяем, что возраст меньше допустимого
        return age < timedelta(minutes=max_age_minutes)
        
    except (ValueError, TypeError):
        # Если время в неверном формате, считаем курс устаревшим
        return False

def print_help():
    """Показывает справку по командам системы управления портфелем."""
    
    print("\n***Система управления портфелем валют***")
    
    print("\n***Регистрация и авторизация***")
    print("register --username <имя> --password <пароль> - регистрация пользователя, пароль должен быть не менее 4-х символов")
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