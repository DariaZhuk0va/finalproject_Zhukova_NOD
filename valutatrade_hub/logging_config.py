import os
from datetime import datetime

LOG_CONFIG = {
    # Уровень логирования
    "LOG_LEVEL": "INFO",  # INFO или DEBUG
    "LOG_FORMAT": "string",  # string (фиксированно строковый)
    # Директории и файлы
    "LOG_DIR": "logs",
    "ACTIONS_LOG": "actions.log",
    "ERRORS_LOG": "errors.log",
    # Ротация файлов
    "LOG_ROTATION_ENABLED": True,
    "LOG_MAX_SIZE_MB": 10,  # 10 MB
    "LOG_BACKUP_COUNT": 5,  # 5 backup файлов
    # Формат timestamp
    "TIMESTAMP_FORMAT": "iso",  # iso: 2025-10-09T12:05:22
    # Какие действия логировать (управляется декоратором)
    "LOG_ACTIONS": ["BUY", "SELL", "REGISTER", "LOGIN"],
}


def setup_logging():
    """Инициализация логирования"""
    log_dir = LOG_CONFIG["LOG_DIR"]
    os.makedirs(log_dir, exist_ok=True)

    # Создаем файлы логов
    for filename in [LOG_CONFIG["ACTIONS_LOG"], LOG_CONFIG["ERRORS_LOG"]]:
        filepath = os.path.join(log_dir, filename)
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Лог файл создан: {datetime.now().isoformat()}\n")


def _should_log():
    """Проверяет уровень логирования"""
    return LOG_CONFIG["LOG_LEVEL"] in ["INFO", "DEBUG"]


def _get_timestamp():
    """Возвращает timestamp в нужном формате"""
    if LOG_CONFIG["TIMESTAMP_FORMAT"] == "iso":
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return datetime.now().isoformat()


def _rotate_log(filepath):
    """Ротация файлов по размеру"""
    if not LOG_CONFIG["LOG_ROTATION_ENABLED"]:
        return

    if not os.path.exists(filepath):
        return

    max_bytes = LOG_CONFIG["LOG_MAX_SIZE_MB"] * 1024 * 1024
    backup_count = LOG_CONFIG["LOG_BACKUP_COUNT"]

    if os.path.getsize(filepath) > max_bytes:
        # Удаляем самый старый backup
        oldest = f"{filepath}.{backup_count}"
        if os.path.exists(oldest):
            os.remove(oldest)

        # Сдвигаем остальные
        for i in range(backup_count - 1, 0, -1):
            old_file = f"{filepath}.{i}"
            new_file = f"{filepath}.{i+1}"
            if os.path.exists(old_file):
                os.rename(old_file, new_file)

        # Текущий файл -> backup.1
        backup_1 = f"{filepath}.1"
        if os.path.exists(backup_1):
            os.remove(backup_1)
        os.rename(filepath, backup_1)

        # Создаем новый
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Файл ротирован: {datetime.now().isoformat()}\n")


def _format_log_string(action, **kwargs):
    """
    Форматирует лог в строковый формат
    """
    # Уровень и timestamp
    log_line = f"INFO {_get_timestamp()} {action} "

    field_order = ["user", "currency", "amount", "rate", "base", "result"]

    # Поля
    fields = []
    for key in field_order:
        if key in kwargs and kwargs[key] is not None:
            value = kwargs[key]

            if key == "amount":
                try:
                    value = f"{float(value):.4f}"
                except Exception:
                    pass
            elif key == "rate":
                try:
                    value = f"{float(value):.2f}"
                except Exception:
                    pass

            if isinstance(value, str) and key in [
                "user",
                "currency",
                "base",
                "result",
                "error_type",
                "error_message",
            ]:
                fields.append(f"{key}='{value}'")
            else:
                fields.append(f"{key}={value}")

    for key, value in kwargs.items():
        if key not in field_order and value is not None:
            if isinstance(value, str) and key in [
                "error_type",
                "error_message",
                "wallet_before",
                "wallet_after",
            ]:
                fields.append(f"{key}='{value}'")
            else:
                fields.append(f"{key}={value}")

    log_line += " ".join(fields)
    return log_line


def log_action(action, **kwargs):
    """
    Логирует действие пользователя
    Формат: строковый
    """
    if not _should_log():
        return

    if action not in LOG_CONFIG["LOG_ACTIONS"]:
        return

    log_dir = LOG_CONFIG["LOG_DIR"]
    filepath = os.path.join(log_dir, LOG_CONFIG["ACTIONS_LOG"])

    # Форматируем строку лога
    log_line = _format_log_string(action, **kwargs)

    # Записываем
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    # Ротация
    _rotate_log(filepath)


def log_error(action, **kwargs):
    """
    Логирует ошибку
    Тот же формат, но result=ERROR
    """
    if not _should_log():
        return

    log_dir = LOG_CONFIG["LOG_DIR"]
    filepath = os.path.join(log_dir, LOG_CONFIG["ACTIONS_LOG"])  # Тот же файл!

    # Устанавливаем result=ERROR
    kwargs["result"] = "ERROR"

    # Форматируем
    log_line = _format_log_string(action, **kwargs)

    # Записываем
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

    _rotate_log(filepath)


def set_log_level(level):
    """Меняет уровень логирования (INFO/DEBUG)"""
    if level.upper() in ["INFO", "DEBUG"]:
        LOG_CONFIG["LOG_LEVEL"] = level.upper()
        print(f"Уровень логирования изменен на: {level}")
    else:
        print(f"Неподдерживаемый уровень: {level}")


def _format_log_string(action, **kwargs):
    """
    Форматирует лог в строковый формат
    Поддерживает currency_code -> currency для совместимости
    """
    # Уровень и timestamp
    log_line = f"INFO {_get_timestamp()} {action} "

    # Поля
    fields = []

    # Обрабатываем currency_code -> currency
    if "currency_code" in kwargs:
        kwargs["currency"] = kwargs.pop("currency_code")

    for key, value in kwargs.items():
        if value is not None:
            # Форматируем числа
            if key == "amount":
                try:
                    value = f"{float(value):.4f}"
                except Exception:
                    pass
            elif key == "rate":
                try:
                    value = f"{float(value):.2f}"
                except Exception:
                    pass

            # Кавычки для строк
            if isinstance(value, str) and key in [
                "user",
                "currency",
                "base",
                "result",
                "error_type",
                "error_message",
            ]:
                # Экранируем кавычки внутри строки
                value = value.replace("'", "\\'")
                fields.append(f"{key}='{value}'")
            else:
                fields.append(f"{key}={value}")

    log_line += " ".join(fields)
    return log_line
