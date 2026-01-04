import os
import shlex

import prompt

from .constants import COMMAND_POSITION, DATA_DIR

from valutatrade_hub.cli.interface import (
    register_command,
    login_command,
    show_portfolio_command,
    buy_command
)

def run():
    """
    Главная функция с основным циклом программы.
    """

    print("Добро пожаловать на Платформу для отслеживания и симуляции торговли валютами!\n")
    #print("Введите 'help' для просмотра доступных команд.")
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

                #case "help":
                    #print_help()

                case "register":
                    USERNAME_POSITION = COMMAND_POSITION + 2
                    PASSWORD_POSITION = COMMAND_POSITION + 4
                    username = args[USERNAME_POSITION]
                    password = args[PASSWORD_POSITION]
                    reg, message = register_command(username, password)
                    print(message)  
                case "login":
                    USERNAME_POSITION = COMMAND_POSITION + 2
                    PASSWORD_POSITION = COMMAND_POSITION + 4
                    username = args[USERNAME_POSITION]
                    password = args[PASSWORD_POSITION]
                    session_data, message = login_command(username, password)
                    print(message)                  
                case "show-portfolio":
                    BASE_POSITION = COMMAND_POSITION + 1
                    if len(args) > 1:
                        base = args[BASE_POSITION]
                    else:
                        base = 'USD' 
                    port, message = show_portfolio_command(session_data, base,)
                    print(message)
                case "buy":
                    BASE_POSITION = COMMAND_POSITION + 2
                    AMOUNT_POSITION = COMMAND_POSITION + 4
                    base = args[BASE_POSITION]
                    try:
                        amount = float(args[AMOUNT_POSITION])
                    except:
                        print("'amount' должен быть числом")
                    buy_status, message = buy_command(session_data, base, amount)
                    print(message)
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