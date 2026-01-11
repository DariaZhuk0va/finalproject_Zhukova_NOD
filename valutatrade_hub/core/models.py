import hashlib
from datetime import datetime

from valutatrade_hub.core.constants import RATES_FILE
from valutatrade_hub.core.exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    InvalidName,
    InvalidPassword,
    WalletNotFoundError,
)
from valutatrade_hub.infra.database import db


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
        salt = hashlib.sha256(
            f"{self._username}{self._user_id}{datetime.now().strftime('%Y%m%d%H%M%S%f')}".encode()
        ).hexdigest()[:6]
        return salt

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с солью"""
        return hashlib.sha256((password + self._salt).encode()).hexdigest()

    def _validate_username(self, username: str):
        """Проверяет имя пользователя"""
        if not username or len(username.strip()) == 0:
            raise InvalidName

    def _validate_password(self, password: str):
        """Проверяет пароль"""
        if len(password) < 4:
            raise InvalidPassword

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
            "registration_date": self._registration_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
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
            raise InvalidAmountError(value)
        self._balance = value

    def deposit(self, amount: float) -> None:
        """Пополнение баланса"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise InvalidAmountError(amount)
        self.balance += amount

    def withdraw(self, amount: float) -> None:
        """Снятие средств"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise InvalidAmountError(amount)
        if amount > self.balance:
            raise InsufficientFundsError(
                currency_code=self.currency_code,
                available=self.balance,
                required=amount,
            )
        self.balance -= amount

    def get_balance_info(self) -> None:
        """Вывод информации о текущем балансе"""
        print(f"Валюта: {self.currency_code}")
        print(f"Баланс: {self.balance:.2f}")

    def to_dict(self) -> dict:
        """Конвертирует кошелёк в словарь для JSON"""
        return {"currency_code": self.currency_code, "balance": self.balance}


class Portfolio:
    """Управление всеми кошельками одного пользователя"""

    def __init__(self, user_id: int, wallets: dict = None):
        """
        Создание портфеля

        Args:
            user_id: Уникальный идентификатор пользователя
        """
        self._user_id = user_id
        self._wallets = wallets if wallets is not None else {}
        self._exchange_rates = self._load_exchange_rates()

    def _load_exchange_rates(self) -> dict:
        """Загружает курсы валют из файла data/rates.json"""

        rates = db.load(RATES_FILE)
        if not rates:
            default_rates = {
                "EUR_USD": {"rate": 1.0786, "updated_at": "2025-10-09T10:30:00"},
                "BTC_USD": {"rate": 59337.21, "updated_at": "2025-10-09T10:29:42"},
                "RUB_USD": {"rate": 0.01016, "updated_at": "2025-10-09T10:31:12"},
                "ETH_USD": {"rate": 3720.00, "updated_at": "2025-10-09T10:35:00"},
                "source": "ParserService",
                "last_refresh": "2025-10-09T10:35:00",
            }
            db.save(RATES_FILE, default_rates)
            print(f"Файл {RATES_FILE} не найден, создан с базовыми курсами")
            return default_rates
        return rates

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
        if currency_code in self._wallets:
            raise ValueError(f"Кошелёк с валютой {currency_code} уже существует")

        wallet = Wallet(currency_code, initial_balance)
        self._wallets[currency_code] = wallet

    def get_wallet(self, currency_code: str):
        """Возвращает объект Wallet по коду валюты"""
        if currency_code not in self._wallets:
            raise WalletNotFoundError(currency_code)
        return self._wallets[currency_code]

    def get_total_value(self, base_currency: str = "USD") -> float:
        """Возвращает общую стоимость всех валют в базовой валюте"""
        rates_data = db.load(RATES_FILE)
        pairs = rates_data.get("pairs", {}) if isinstance(rates_data, dict) else {}
    
        total_value = 0.0

        for currency_code, wallet in self._wallets.items():
            if currency_code == base_currency:
                total_value += wallet.balance
                continue
            
        # Ищем курс для конвертации
            rate_key = f"{currency_code}_{base_currency}"
            if rate_key in pairs:
                pair_data = pairs[rate_key]
                rate = (pair_data.get("rate", 0) 
                        if isinstance(pair_data, dict) else pair_data)
            else:
                # Пробуем обратный курс
                reverse_key = f"{base_currency}_{currency_code}"
                if reverse_key in pairs:
                    pair_data = pairs[reverse_key]
                    reverse_rate = (pair_data.get("rate", 0) 
                                    if isinstance(pair_data, dict) else pair_data)
                    rate = 1 / reverse_rate if reverse_rate != 0 else 0
                else:
                    print(f"Курс для {currency_code}→{base_currency} "
                          "не найден, пропускаем")
                    continue
        
            if rate == 0:
                print(f"Нулевой курс для {currency_code}→{base_currency}, пропускаем")
                continue
            
            total_value += wallet.balance * rate

        return round(total_value, 2)

    def to_dict(self) -> dict:
        """Конвертирует портфель в словарь для JSON"""
        wallets_dict = {}
        for currency_code, wallet in self._wallets.items():
            wallets_dict[currency_code] = wallet.to_dict()

        return {"user_id": self._user_id, "wallets": wallets_dict}

    @classmethod
    def from_dict(cls, data: dict):
        """Создает Portfolio из словаря"""
        user_id = data["user_id"]
        wallets_data = data.get("wallets", {})

        wallets = {}
        for currency_code, wallet_data in wallets_data.items():
            wallet = Wallet(
                currency_code=currency_code, balance=wallet_data.get("balance", 0.0)
            )
            wallets[currency_code] = wallet

        return cls(user_id, wallets)
