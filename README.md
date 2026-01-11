Valutatrade Hub - это консольное приложение для управления личным валютным портфелем. С помощью приложения вы можете отслеживать курсы валют и криптовалют, покупать и продавать активы, а также просматривать стоимость своего портфеля в разных валютах. Приложение получает актуальные курсы от CoinGecko (криптовалюты) и ExchangeRate-API (фиатные валюты).

СТРУКТУРА КАТАЛОГОВ
text
valutatrade_hub/
├── core/                    # Ядро приложения
│   ├── constants.py        # Константы
│   ├── currencies.py       # Управление валютами
│   ├── exceptions.py       # Пользовательские исключения
│   ├── models.py           # Модели данных
│   ├── usecases.py         # Бизнес-логика
│   └── utils.py            # Утилиты
├── infra/                  # Инфраструктура
│   ├── config.json         # Конфигурация
│   ├── database.py         # Работа с JSON БД
│   └── settings.py         # Настройки
├── parser_service/         # Сервис парсинга курсов
│   ├── api_clients.py      # API клиенты
│   ├── config.py           # Конфигурация парсера
│   ├── storage.py          # Хранение курсов
│   ├── updater.py          # Обновление курсов
│   └── scheduler.py        # Планировщик обновлений
├── cli/                    # Интерфейс командной строки
│   └── interface.py        # CLI команды
├── decorators.py           # Декораторы логирования
├── logging_config.py       # Конфигурация логирования
├── main.py                 # Точка входа
└── __init__.py

data/                       # Данные (создается автоматически)
├── users.json              # Пользователи
├── portfolios.json         # Портфели
├── rates.json              # Курсы валют
└── logs/                   # Логи приложения
    ├── actions.log         # Логи действий
    └── errors.log          # Логи ошибок


Установка
Установка зависимостей:
bash
make install
или

bash
poetry install
Запуск:
bash
make run
или

bash
poetry run project
Сборка пакета:
bash
make build
или

bash
poetry build
Публикация (тестовый режим):
bash
make publish
или

bash
poetry publish --dry-run
Установка пакета локально:
bash
make package-install
или

bash
python3 -m pip install dist/*.whl
Проверка кода:
bash
make lint
или

bash
poetry run ruff check .
Примеры команд CLI
Регистрация и вход
bash
# Регистрация нового пользователя
register --username alice --password securepass123

# Вход в систему
login --username alice --password securepass123
Управление курсами валют
bash
# Обновить курсы валют
update-rates

# Показать все курсы
show-rates

# Показать топ-10 курсов
show-rates --top 10

# Показать курсы для конкретной валюты
show-rates --currency BTC
show-rates --currency EUR

# Получить курс между двумя валютами
get-rate --from BTC --to USD
get-rate --from EUR --to RUB
Операции с портфелем
bash
# Показать портфель в USD
show-portfolio

# Показать портфель в другой валюте
show-portfolio --base EUR
show-portfolio --base RUB

# Купить валюту
buy --currency BTC --amount 0.5
buy --currency EUR --amount 1000

# Продать валюту
sell --currency USD --amount 500
sell --currency ETH --amount 2.0
Система кэширования и TTL
Кэширование курсов валют
Приложение использует интеллектуальное кэширование курсов валют:

Кэширование API запросов: Результаты API запросов к CoinGecko и ExchangeRate-API кэшируются локально

TTL (Time To Live): По умолчанию курсы кэшируются на 5 минут (300 секунд)

Автоматическое обновление: При запросе курса проверяется время последнего обновления, если данные устарели - выполняется автоматическое обновление

Настройка TTL
TTL настраивается в файле конфигурации valutatrade_hub/infra/config.json:

json
{
  "RATES_TTL_SECONDS": 300,
  "DEFAULT_BASE_CURRENCY": "USD"
}
Работа кэша
text
>>> get-rate --from BTC --to USD
# Первый запрос - получаем данные из API и кэшируем

>>> get-rate --from BTC --to USD  
# Повторный запрос в течение 5 минут - данные из кэша

>>> update-rates
# Принудительное обновление - кэш очищается

>>> get-rate --from BTC --to USD
# После 5 минут - данные устарели, получаем свежие из API
Включение Parser Service и хранение API ключа
1. Получение API ключа
Для работы с фиатными валютами нужен API ключ от ExchangeRate-API:

Перейдите на сайт: https://app.exchangerate-api.com/

Зарегистрируйтесь бесплатно (до 1500 запросов в месяц)

Получите ваш API ключ

2. Настройка API ключа
Создайте файл .env в корневой директории проекта:

bash
# .env файл
EXCHANGERATE_API_KEY=ваш_ключ_здесь
3. Запуск Parser Service
Parser Service включается автоматически при выполнении команд:

bash
# Запускает обновление курсов
update-rates

# Или принудительное обновление из конкретного источника
update-rates --source coinmarketcap
update-rates --source exchangerate-api
4. Автоматическое обновление
Для периодического обновления курсов можно использовать планировщик:

python
# Пример запуска планировщика (каждые 6 часов)
from valutatrade_hub.parser_service.scheduler import create_scheduler
scheduler = create_scheduler(interval_hours=6)
scheduler.start()
5. Просмотр статистики кэша
bash
# Приложение автоматически ведет статистику кэширования
# Данные сохраняются в data/exchange_rates.json
Демонстрация работы
Пример сессии работы
text
$ poetry run project
>>> register --username investor --password invest123
Пользователь 'investor' зарегистрирован (id=1). Войдите: login --username investor --password ****

>>> login --username investor --password invest123
Вы вошли как 'investor'

>>> update-rates
Starting rates update...
Fetching from CoinGecko... OK (10 rates)
Fetching from ExchangeRate-API... OK (32 rates)
Update successful. Total rates updated: 42

>>> show-rates --top 5
+----------+----------+----------------+
|   From   |    To    |      Rate      |
+----------+----------+----------------+
|   BTC    |   USD    |   59337.21     |
|   ETH    |   USD    |    3720.00     |
|   EUR    |   USD    |     1.0786     |
|   GBP    |   USD    |     1.2642     |
|   JPY    |   USD    |    0.00638     |
+----------+----------+----------------+

>>> buy --currency USD --amount 1000
Покупка выполнена: 1000.0000 USD по курсу 1.00 USD/USD

>>> buy --currency BTC --amount 0.1
Покупка выполнена: 0.1000 BTC по курсу 59337.21 USD/BTC

>>> show-portfolio
+----------+----------+--------------+------------------+
| Валюта   | Баланс   | Курс к USD   | Стоимость в USD  |
+----------+----------+--------------+------------------+
| USD      | 1000.00  |     1.00     |     1000.00      |
| BTC      |   0.10   |   59337.21   |     5933.72      |
+----------+----------+--------------+------------------+
ИТОГО: 6,933.72 USD

>>> get-rate --from BTC --to EUR
Курс BTC→EUR: 55023.45678901
Обновлено: 2025-10-09 12:30:45
Обратный курс EUR→BTC: 0.00001817

>>> exit
Особенности системы
Безопасность
Пароли хранятся в хешированном виде с использованием SHA-256 и соли

Сессии пользователей управляются через безопасные токены

Логирование
Все действия пользователей логируются в logs/actions.log

Ошибки сохраняются в logs/errors.log

Автоматическая ротация логов (10 MB, 5 backup файлов)

Обработка ошибок
Пользовательские исключения с понятными сообщениями

Отказоустойчивость при недоступности API

Автоматическое использование кэшированных данных при ошибках сети

Поддерживаемые валюты
Фиатные валюты: USD, EUR, RUB, GBP, JPY, CHF, CAD, AUD и другие

Криптовалюты: BTC, ETH, BNB, XRP, SOL, DOGE, ADA, AVAX, DOT, TRX

Valutatrade Hub - простое и мощное решение для управления вашим валютным портфелем прямо из терминала!
