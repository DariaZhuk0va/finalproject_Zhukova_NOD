class InsufficientFundsError(Exception):
    """
    Недостаточно средств на кошельке
    """

    def __init__(self, currency_code: str, available: float, required: float):
        self.currency_code = currency_code
        self.available = available
        self.required = required
        message = (f"Недостаточно средств: доступно {available:.4f} {currency_code}, "
                   f"требуется {required:.4f} {currency_code}")
        super().__init__(message)


class CurrencyNotFoundError(Exception):
    """
    Валюта не найдена
    """

    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        message = f"Неизвестная валюта '{currency_code}'"
        super().__init__(message)


class ApiRequestError(Exception):
    """
    Ошибка при обращении к внешнему API
    """

    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class UserNotAuthenticatedError(Exception):
    """
    Пользователь не аутентифицирован
    """

    def __init__(self):
        message = "Сначала выполните login"
        super().__init__(message)


class WalletNotFoundError(Exception):
    """
    Кошелек с указанной валютой не найден
    """

    def __init__(self, currency_code: str):
        self.currency_code = currency_code
        message = f"Кошелька с валютой '{currency_code}' не существует"
        super().__init__(message)


class InvalidAmountError(Exception):
    """
    Некорректная сумма операции
    """

    def __init__(self, amount: float):
        self.amount = amount
        message = (
            f"Некорректная сумма: {amount}. Сумма должна быть положительным числом"
        )
        super().__init__(message)


class InvalidName(Exception):
    """
    Некорректное имя
    """

    def __init__(self):
        message = "Имя пользователя не может быть пустым"
        super().__init__(message)


class InvalidPassword(Exception):
    """
    Некорректный формат пароля
    """

    def __init__(self):
        message = "Пароль должен быть не короче 4 символов"
        super().__init__(message)
