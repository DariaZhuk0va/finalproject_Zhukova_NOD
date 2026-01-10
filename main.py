#!/usr/bin/env python3
import shlex

import prompt

from valutatrade_hub.cli.interface import (
    buy_command,
    get_rate_command,
    login_command,
    register_command,
    sell_command,
    show_portfolio_command,
    show_rates_command,
    update_rates_command,
)
from valutatrade_hub.core.constants import COMMAND_POSITION
from valutatrade_hub.core.utils import initialize_files, print_help


def run():
    """
    Главная функция с основным циклом программы.
    """
    initialize_files()

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
                    if len(args) == 3 and args[COMMAND_POSITION + 1] == "--base":
                        BASE_POSITION = COMMAND_POSITION + 2
                        base = args[BASE_POSITION]
                        result = show_portfolio_command(session_data, base)
                        print(result["message"])
                    elif len(args) == 1:
                        base = "USD"
                        result = show_portfolio_command(session_data, base)
                        print(result["message"])
                    else:
                        print("Неверный формат команды")
                        print(
                            'show-portfolio [--base <валюта>]'
                        )

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
                case "update-rates":
                    if len(args) == 3 and args[COMMAND_POSITION + 1] == "--source":
                        SOURCE_POSITION = COMMAND_POSITION + 2
                        source = args[SOURCE_POSITION]
                        if source not in ["coingecko", "exchangerate"]:
                            print("Неверный источник. Допустимые значения: "
                                  "coingecko, exchangerate")
                        else:
                            result = update_rates_command(source=source)
                            print(result["message"])
                    elif len(args) == 1:
                        result = update_rates_command()
                        print(result["message"])
                    else:
                        print("Неверный формат команды")
                        print(
                            "Правильный формат: update-rates "
                            "[--source <coingecko|exchangerate>]"
                        )               
                case "show-rates":
                    currency = None
                    top = None
                    base = "USD"
                    
                    i = 1
                    while i < len(args):
                        if args[i] == "--currency" and i + 1 < len(args):
                            currency = args[i + 1]
                            i += 2
                        elif args[i] == "--top" and i + 1 < len(args):
                            try:
                                top = int(args[i + 1])
                                if top <= 0:
                                    print("Значение --top должно быть "
                                          "положительным числом")
                                    top = None
                            except ValueError:
                                print("Значение --top должно быть числом")
                            i += 2
                        elif args[i] == "--base" and i + 1 < len(args):
                            base = args[i + 1]
                            i += 2
                        else:
                            print(f"Неизвестный аргумент: {args[i]}")
                            break
                    
                    result = show_rates_command(currency=currency, top=top, base=base)
                    print(result["message"])
                
                case _:
                    print(f"Функции '{command}' нет. Попробуйте снова.")
                    print("Введите 'help' для просмотра доступных команд.")

        except KeyboardInterrupt:
            print("\n\nПрограмма прервана пользователем. До свидания!")
            break
        except EOFError:
            print("\nДо свидания!")
            break

def main():
    run()


if __name__ == "__main__":
    main()