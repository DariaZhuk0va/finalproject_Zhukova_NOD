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
    
    
    
    