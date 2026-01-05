import json
import os


class DatabaseManager:
    """
    Простейший менеджер для работы с JSON файлами.
    Singleton через __new__ - самый простой способ.
    """
    
    _instance = None  # Храним единственный экземпляр
    
    def __new__(cls):
        """Гарантируем только один экземпляр"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Инициализация (один раз)"""
        if hasattr(self, 'data_dir'):
            return  # Уже инициализирован
        
        self.data_dir = 'data'  # Папка для файлов
        os.makedirs(self.data_dir, exist_ok=True)  # Создаем если нет
    
    def load(self, filename: str):
        """
        Прочитать данные из JSON файла.
        
        Args:
            filename: Имя файла (например, 'users.json')
            
        Returns:
            Данные из файла или [] если файла нет
        """
        path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(path):
            return {}  # Файла нет - возвращаем пустой список
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}  # Если ошибка чтения
    
    def save(self, filename: str, data):
        """
        Сохранить данные в JSON файл.
        
        Args:
            filename: Имя файла
            data: Данные для сохранения
        """
        path = os.path.join(self.data_dir, filename)
        
        try:
            # Создаем временный файл для безопасной записи
            temp_path = path + '.tmp'
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Заменяем старый файл новым
            if os.path.exists(path):
                os.remove(path)
            os.rename(temp_path, path)
            
        except Exception as e:
            print(f"Ошибка сохранения {filename}: {e}")


# Создаем единственный экземпляр для всего приложения
db = DatabaseManager()