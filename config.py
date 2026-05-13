from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HISTORICO_DIR = DATA_DIR / "historico"

PORTFOLIO_FILE = DATA_DIR / "portfolio.json"
FUNDAMENTALES_FILE = HISTORICO_DIR / "fundamentales.csv"

# yfinance agrega sufijo .MX para BMV
TICKER_SUFFIX = ".MX"

PAGE_TITLE = "FIBRAs Tracker"
PAGE_ICON = "🏢"
