from pathlib import Path


# Path configurations
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORICO_DIR = DATA_DIR / "historico"

POSITIONS_FILE = DATA_DIR / "positions.json"
DISTRIBUTIONS_FILE = DATA_DIR / "distributions.json"
FUNDAMENTALES_FILE = HISTORICO_DIR / "fundamentales.csv"

# yfinance adds suffix .MX for BMV
TICKER_SUFFIX = ".MX"

PAGE_TITLE = "FIBRALens"
PAGE_ICON = "ui/assets/fibralens_logo_light_v2.svg"

# Withholding tax rate for fiscal result income in Mexico
FISCAL_RESULT_WITHHOLDING_RATE = 0.30
