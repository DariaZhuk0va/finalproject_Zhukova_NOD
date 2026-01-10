from valutatrade_hub.infra.settings import settings

DATA_DIR = settings.get("DATA_DIR", "data")
COMMAND_POSITION = settings.get("COMMAND_POSITION", 0)
RATES_FILE = settings.get("RATES_FILE", "rates.json")
USERS_FILE = settings.get("USERS_FILE", "users.json")
PORTFOLIOS_FILE = settings.get("PORTFOLIOS_FILE", "portfolios.json")

