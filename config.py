from pathlib import Path


# Path configurations
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORICO_DIR = DATA_DIR / "historico"

POSITIONS_DATA_PATH = DATA_DIR / "positions.json"
DISTRIBUTIONS_DATA_PATH = DATA_DIR / "distributions.json"
FUNDAMENTALS_DATA_PATH = DATA_DIR / "historical" / "fundamentals.json"
CATALOG_DATA_PATH = DATA_DIR / "catalog.json"

# yfinance adds suffix .MX for BMV
TICKER_SUFFIX = ".MX"

PAGE_ICON = "ui/assets/fibralens_logo_light_v2.svg"
PAGE_TITLE = "FIBRALens"
PAGE_LEGEND = "Tu herramienta de análisis para FIBRAs mexicanas"

# Withholding tax rate for fiscal result income in Mexico
FISCAL_RESULT_WITHHOLDING_RATE = 0.30
