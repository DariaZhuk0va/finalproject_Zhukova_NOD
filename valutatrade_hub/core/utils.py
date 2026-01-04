import json
import os
from datetime import datetime
from datetime import timedelta

def ensure_data_dir():
    """Создает папку data если её нет"""
    os.makedirs("data", exist_ok=True)


def load_json(filename: str, default=None):
    """Загружает данные из JSON файла в папке data"""
    ensure_data_dir()
    
    if default is None:
        default = []
    
    filepath = os.path.join("data", filename)
    if not os.path.exists(filepath):
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(filename: str, data):
    """Сохраняет данные в JSON файл в папке data"""
    ensure_data_dir()
    
    filepath = os.path.join("data", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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