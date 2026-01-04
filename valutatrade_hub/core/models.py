import hashlib
from datetime import datetime
import json
import os


class User:
    """Класс пользователя"""
    
    def __init__(self, user_id: int, username: str, password: str):
        """
        Создание пользователя
        
        Args:
            user_id: Уникальный ID
            username: Имя пользователя
            password: Пароль (будет захеширован)
        """
        self._user_id = user_id
        self._username = username
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(password)
        self._registration_date = datetime.now()
    
    def _generate_salt(self) -> str:
        """Генерирует соль"""
        salt = hashlib.sha256(f"{self._username}{self._user_id}{datetime.now().strftime('%Y%m%d%H%M%S%f')}".encode()).hexdigest()[:6]
        return salt
    
    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с солью"""
        return hashlib.sha256((password + self._salt).encode()).hexdigest()
    
    def _validate_username(self, username: str):
        """Проверяет имя пользователя"""
        if not username or len(username.strip()) == 0:
            raise ValueError("Имя пользователя не может быть пустым")
    
    def _validate_password(self, password: str):
        """Проверяет пароль"""
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
    
    @property
    def user_id(self) -> int:
        """Получить ID пользователя"""
        return self._user_id
    
    @property
    def username(self) -> str:
        """Получить имя пользователя"""
        return self._username
    
    @username.setter
    def username(self, value: str):
        """Установить имя пользователя"""
        self._validate_username(value)
        self._username = value
    
    @property
    def salt(self) -> str:
        """Получить соль"""
        return self._salt
    
    @property
    def hashed_password(self) -> str:
        """Получить хешированный пароль"""
        return self._hashed_password
    
    @property
    def password(self) -> str:
        """Получить пароль (маскированный)"""
        return "********"

    @password.setter
    def password(self, value: str):
        """Сеттер для пароля - хеширует пароль автоматически"""
        self._validate_password(value)
        # Генерируем новую соль для нового пароля
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(value)
    
    @property
    def registration_date(self) -> datetime:
        """Получить дату регистрации"""
        return self._registration_date
    
    def get_user_info(self) -> None:
        """Выводит информацию о пользователе (без пароля)"""
        print(f"ID пользователя: {self._user_id}")
        print(f"Имя пользователя: {self._username}")
        print(f"Дата регистрации: {self._registration_date.strftime('%d.%m.%Y %H:%M')}")
    
    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя"""
        self.password = new_password
    
    def verify_password(self, password: str) -> bool:
        """Проверяет введенный пароль"""
        return self._hash_password(password) == self._hashed_password
    
    def to_dict(self) -> dict:
        """Конвертирует в словарь для сохранения в JSON"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Создать пользователя из словаря"""
        # Создаем временный объект
        user = cls.__new__(cls)
    
        # Устанавливаем атрибуты напрямую
        user._user_id = data["user_id"]
        user._username = data["username"]
        user._hashed_password = data["hashed_password"]
        user._salt = data["salt"]
        user._registration_date = datetime.fromisoformat(data["registration_date"])
    
        return user
    
class Wallet:
    """Кошелёк пользователя для одной валюты"""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Создание кошелька
        
        Args:
            currency_code: Код валюты (например, "USD", "BTC")
            balance: Начальный баланс (по умолчанию 0.0)
        """
        self.currency_code = currency_code
        self._balance = balance
    
    @property
    def balance(self) -> float:
        """Получить текущий баланс"""
        return self._balance
    
    @balance.setter
    def balance(self, value: float):
        """Установить баланс (запрещает отрицательные значения)"""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value
    
    def deposit(self, amount: float) -> None:
        """Пополнение баланса"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self.balance += amount
    
    def withdraw(self, amount: float) -> None:
        """Снятие средств"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")
        if amount > self.balance:
            raise ValueError("Недостаточно средств на балансе")
        self.balance -= amount
    
    def get_balance_info(self) -> None:
        """Вывод информации о текущем балансе"""
        print(f"Валюта: {self.currency_code}")
        print(f"Баланс: {self.balance:.2f}")
    
    def to_dict(self) -> dict:
        """Конвертирует кошелёк в словарь для JSON"""
        return {
            "currency_code": self.currency_code,
            "balance": self.balance
        }
    
class Portfolio:
    """Управление всеми кошельками одного пользователя"""
    
    def __init__(self, user_id: int):
        """
        Создание портфеля
        
        Args:
            user_id: Уникальный идентификатор пользователя
        """
        self._user_id = user_id
        self._wallets = {}  # dict[str, Wallet]
        self._exchange_rates = self._load_exchange_rates()
    
    def _load_exchange_rates(self) -> dict:
        """Загружает курсы валют из файла data/rates.json"""
        RATES_FILE = "data/rates.json"
        
        # Если файла нет, создаем с базовыми курсами
        if not os.path.exists(RATES_FILE):
            default_rates = {
                            "EUR_USD": {
                            "rate": 1.0786,                  
                            "updated_at": "2025-10-09T10:30:00"
                            },
                            "BTC_USD": {
                            "rate": 59337.21,                
                            "updated_at": "2025-10-09T10:29:42"
                            },
                            "RUB_USD": {
                            "rate": 0.01016,                 
                            "updated_at": "2025-10-09T10:31:12"
                            },
                            "ETH_USD": {
                            "rate": 3720.00,                 
                            "updated_at": "2025-10-09T10:35:00"
                            },
                            "source": "ParserService",         
                            "last_refresh": "2025-10-09T10:35:00"  
                            } 
            os.makedirs("data", exist_ok = True)
            with open(RATES_FILE, 'w') as f:
                json.dump(default_rates, f, indent = 2)
            print(f"Файл {RATES_FILE} не найден, создан с базовыми курсами")
            return default_rates
        
        # Загружаем курсы из файла
        try:
            with open(RATES_FILE, 'r') as f:
                rates = json.load(f)
            return rates
        except Exception as e:
            print(f"Ошибка загрузки курсов: {e}")
            return {"USD": 1.0}
    
    @property
    def user_id(self) -> int:
        """Получить ID пользователя"""
        return self._user_id
    
    @property
    def wallets(self) -> dict:
        """Получить копию словаря кошельков"""
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> None:
        """Добавляет новый кошелёк в портфель"""
        from models import Wallet
        
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк с валютой {currency_code} уже существует")
        
        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet
    
    def get_wallet(self, currency_code: str):
        """Возвращает объект Wallet по коду валюты"""
        if currency_code not in self._wallets:
            raise ValueError(f"Кошелёк с валютой {currency_code} не найден")
        return self._wallets[currency_code]
    
    def get_total_value(self, base_currency: str = "USD") -> float:
        """Возвращает общую стоимость всех валют в базовой валюте"""
        if base_currency not in self._exchange_rates:
            raise ValueError(f"Курс для валюты {base_currency} не найден")
        
        total_value = 0.0
        
        for currency_code, wallet in self._wallets.items():
            if currency_code not in self._exchange_rates:
                print(f"Курс для {currency_code} не найден, пропускаем")
                continue
            
            # Конвертируем в базовую валюту
            if currency_code == base_currency:
                total_value += wallet.balance
            else:
                value_in_base = wallet.balance * self._exchange_rates[currency_code]
                total_value += value_in_base
        
        return round(total_value, 2)
    
    def to_dict(self) -> dict:
        """Конвертирует портфель в словарь для JSON"""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()
        
        return {
            "user_id": self._user_id,
            "wallets": wallets_dict
        }
    