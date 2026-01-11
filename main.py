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
from valutatrade_hub.parser_service.scheduler import RateScheduler
from valutatrade_hub.infra.settings import settings


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

    if settings.get("SCHEDULER_AUTO_START", False):
        interval = settings.get("SCHEDULER_INTERVAL_HOURS", 6)
        scheduler = RateScheduler(interval_hours = interval)
        scheduler.start()
        print(f"Автоматическое обновление запущено (интервал: {interval} ч)")

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
                    COMMAND_LIST = (1, 3, 5)
                    count_cur_com = args.count('--currency')
                    count_top_com = args.count('--top')
                    count_base_com = args.count('--base')
                    total_len = 0

                    if len(args) == 1:
                        result = show_rates_command()
                        print(result["message"])
                        continue 
                    else:
                        if count_cur_com in (0,1) or count_top_com in (0,1) or count_base_com in (0,1):
                            total_len = 1 + (count_cur_com + count_top_com + count_base_com) * 2
                        if len(args) == total_len:
                            if count_cur_com == 1 and args.index('--currency') in COMMAND_LIST:
                                param_position = args.index('--currency') + 1
                                currency = args[param_position]
                            if count_top_com == 1 and args.index('--top') in COMMAND_LIST:
                                param_position = args.index('--top') + 1
                                top = args[param_position]
                                try:
                                    top = int(top)
                                    if top <= 0:
                                        print("Значение --top должно быть "
                                              "положительным числом")
                                        continue
                                except ValueError:
                                    print("Значение --top должно быть числом")
                                    continue
                            if count_base_com == 1 and args.index('--base') in COMMAND_LIST:
                                param_position = args.index('--base') + 1
                                base = args[param_position]  
                            
                            result = show_rates_command(currency=currency, top=top, base=base)
                            print(result["message"])
                        else:
                            print("Неверный формат команды")
                            print(
                                "Правильный формат: show-rates [--currency <валюта>] "
                                "[--top <число>] [--base <валюта>]"
                            )
                            continue   
                    
                
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