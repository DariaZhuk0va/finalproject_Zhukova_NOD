import shlex

import prompt

from valutatrade_hub.cli.interface import (
    buy_command,
    get_rate_command,
    login_command,
    register_command,
    sell_command,
    show_portfolio_command,
)
from valutatrade_hub.core.utils import print_help

from .constants import COMMAND_POSITION


def run():
    """
    Главная функция с основным циклом программы.
    """

    print(
        "Добро пожаловать на Платформу для отслеживания и "
        "симуляции торговли валютами!\n"
    )
    print("Введите 'help' для просмотра доступных команд.")
    print("Введите 'exit' для выхода из программы.")

    session_data = {}

    while True:

        try:

            user_input = prompt.string("\n>>>Введите команду: ").strip()

            if user_input.lower() in ["exit", "quit", "выход"]:
                print("До свидания!")
                break

            if not user_input:
                continue

            try:
                args = shlex.split(user_input)
            except ValueError as e:
                if "No closing quotation" in str(e):
                    print("Ошибка: Незакрытая кавычка в команде")
                else:
                    print(f"Ошибка синтаксиса: {e}")
                continue

            command = args[COMMAND_POSITION].lower()

            match command:

                case "help":
                    print_help()

                case "register":
                    if (
                        len(args) == 5
                        and args[COMMAND_POSITION + 1] == "--username"
                        and args[COMMAND_POSITION + 3] == "--password"
                    ):
                        USERNAME_POSITION = COMMAND_POSITION + 2
                        PASSWORD_POSITION = COMMAND_POSITION + 4
                        username = args[USERNAME_POSITION]
                        password = args[PASSWORD_POSITION]
                        result = register_command(username, password)
                        print(result["message"])
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: register --username <username> "
                            "--password <password>"
                        )

                case "login":
                    if (
                        len(args) == 5
                        and args[COMMAND_POSITION + 1] == "--username"
                        and args[COMMAND_POSITION + 3] == "--password"
                    ):
                        USERNAME_POSITION = COMMAND_POSITION + 2
                        PASSWORD_POSITION = COMMAND_POSITION + 4
                        username = args[USERNAME_POSITION]
                        password = args[PASSWORD_POSITION]
                        result = login_command(username, password)
                        print(result["message"])
                        if result["success"]:
                            session_data = result["data"]
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: login --username <username> "
                            "--password <password>"
                        )

                case "logout":
                    print("Вы вышли из аккаунта")
                    session_data = {}

                case "show-portfolio":
                    BASE_POSITION = COMMAND_POSITION + 1
                    if len(args) > 1:
                        base = args[BASE_POSITION]
                    else:
                        base = "USD"
                    result = show_portfolio_command(session_data, base)
                    print(result["message"])

                case "buy":
                    if (
                        len(args) == 5
                        and args[COMMAND_POSITION + 1] == "--currency"
                        and args[COMMAND_POSITION + 3] == "--amount"
                    ):
                        BASE_POSITION = COMMAND_POSITION + 2
                        AMOUNT_POSITION = COMMAND_POSITION + 4
                        currency = args[BASE_POSITION]
                        try:
                            amount = float(args[AMOUNT_POSITION])
                            result = buy_command(session_data, currency, amount)
                            print(result["message"])
                        except ValueError:
                            print("'amount' должен быть числом")
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: buy --currency "
                            "<currency> --amount <amount>"
                        )

                case "sell":
                    if (
                        len(args) == 5
                        and args[COMMAND_POSITION + 1] == "--currency"
                        and args[COMMAND_POSITION + 3] == "--amount"
                    ):
                        BASE_POSITION = COMMAND_POSITION + 2
                        AMOUNT_POSITION = COMMAND_POSITION + 4
                        currency = args[BASE_POSITION]
                        try:
                            amount = float(args[AMOUNT_POSITION])
                            result = sell_command(session_data, currency, amount)
                            print(result["message"])
                        except ValueError:
                            print("'amount' должен быть числом")
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: sell --currency <currency> "
                            "--amount <amount>"
                        )

                case "get-rate":
                    if (
                        len(args) == 5
                        and args[COMMAND_POSITION + 1] == "--from"
                        and args[COMMAND_POSITION + 3] == "--to"
                    ):
                        FROM_POSITION = COMMAND_POSITION + 2
                        TO_POSITION = COMMAND_POSITION + 4
                        from_rate = args[FROM_POSITION]
                        to_rate = args[TO_POSITION]
                        result = get_rate_command(from_rate, to_rate)
                        print(result["message"])
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: get-rate --from "
                            "<currency> --to <currency>"
                        )

                case _:
                    print(f"Функции '{command}' нет. Попробуйте снова.")
                    print("Введите 'help' для просмотра доступных команд.")

        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем. До свидания!")
            break
        except EOFError:
            print("\nДо свидания!")
            break


if __name__ == "__main__":
    run()
