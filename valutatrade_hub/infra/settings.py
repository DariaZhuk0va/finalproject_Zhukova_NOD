import json
import os


class SettingsLoader:
    """
    Singleton для загрузки и управления конфигурацией.
    
    КОММЕНТАРИЙ ПО ВЫБОРУ РЕАЛИЗАЦИИ:
    
    Выбрана реализация через __new__ по следующим причинам:
    
    1. ПРОСТОТА: Всего 5 строк кода для реализации Singleton
    2. ЧИТАЕМОСТЬ: Любой Python-разработчик сразу понимает логику
    3. ЯВНОСТЬ: Четко видно, что это Singleton в объявлении класса
    4. ПИТОНИЧНОСТЬ: Использует стандартные механизмы Python без "магии"
    5. МИНИМАЛИЗМ: Нет сложных метаклассов или декораторов
    """
    
    # Статическая переменная для хранения единственного экземпляра
    _instance = None
    
    def __new__(cls):
        """
        Переопределение __new__ для контроля создания экземпляров.
        
        Этот метод вызывается ДО __init__ и создает сам объект.
        Мы перехватываем создание и гарантируем только один экземпляр.
        """
        # Если экземпляр еще не создан
        if cls._instance is None:
            # Создаем новый экземпляр
            cls._instance = super().__new__(cls)
        
        # Всегда возвращаем один и тот же экземпляр
        return cls._instance
    
    def __init__(self):
        """
        Инициализация экземпляра.
        Выполняется только один раз благодаря проверке в __new__.
        """
        # Защита от повторной инициализации
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Конфигурация по умолчанию
        self._config = {
            # Пути к данным
            'DATA_DIR': 'data',
            'RATES_FILE': 'rates.json',
            'USERS_FILE': 'users.json',
            'PORTFOLIOS_FILE': 'portfolios.json',
            'CONFIG_FILE': 'valutatrade_hub/infra/config.json',  # Файл конфигурации
            
            # Настройки курсов
            'RATES_TTL_SECONDS': 300,  # 5 минут
            'DEFAULT_BASE_CURRENCY': 'USD',
            
            # Настройки логов
            'LOG_DIR': 'logs',
            'LOG_LEVEL': 'INFO',
            
            # Список поддерживаемых валют
            'SUPPORTED_CURRENCIES': ['USD', 'EUR', 'RUB', 'BTC', 'ETH']
        }
        
        self._create_directories()

        # Создаем файл конфигурации по умолчанию если его нет
        self._create_default_config()
        
        # Загружаем пользовательскую конфигурацию
        self._load_user_config()
        
        # Помечаем как инициализированный
        self._initialized = True
    
    def _create_directories(self):
        """Создает необходимые директории"""
        os.makedirs(self._config['DATA_DIR'], exist_ok=True)
        os.makedirs(self._config['LOG_DIR'], exist_ok=True)

    def _create_default_config(self):
        """Создает файл конфигурации по умолчанию если его нет"""
        config_file = self._config['CONFIG_FILE']
        
        if not os.path.exists(config_file):
            try:
                # Создаем словарь только с основными настройками (без путей к файлам)
                default_config = self._config
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=2, ensure_ascii=False)
                
                print(f"Создан файл конфигурации по умолчанию: {config_file}")
            except Exception as e:
                print(f"Ошибка создания файла конфигурации: {e}")
    
    def _load_user_config(self):
        """Загружает конфигурацию из config.json"""
        config_file = self._config['CONFIG_FILE']
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                self._config.update(user_config)
                print(f"Конфигурация загружена из {config_file}")
            except json.JSONDecodeError:
                print(f"Ошибка: {config_file} содержит некорректный JSON")
            except Exception as e:
                print(f"Ошибка загрузки {config_file}: {e}")
        else:
            print(f"Файл конфигурации {config_file} не найден, используются настройки по умолчанию")
    
    def get(self, key: str, default=None):
        """
        Получить значение конфигурации по ключу.
        
        Args:
            key: Ключ конфигурации (например, 'DATA_DIR')
            default: Значение по умолчанию если ключ не найден
            
        Returns:
            Значение конфигурации или default
        """
        return self._config.get(key, default)

# Создаем глобальный экземпляр при импорте модуля
# Это гарантирует единственный экземпляр во всем приложении
settings = SettingsLoader()