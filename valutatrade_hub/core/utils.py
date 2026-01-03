import json
import os

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