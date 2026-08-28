from pathlib import Path

from dotenv import load_dotenv


# Path configurations
BASE_DIR = Path(__file__).parent

# Load variables from a local .env in the repo root before anything else reads the environment
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)
DATA_DIR = BASE_DIR / "data"
HISTORICO_DIR = DATA_DIR / "historico"

POSITIONS_DATA_PATH = DATA_DIR / "positions.json"
DISTRIBUTIONS_DATA_PATH = DATA_DIR / "distributions.json"
FUNDAMENTALS_DATA_PATH = DATA_DIR / "fundamentals.json"
CATALOG_DATA_PATH = DATA_DIR / "catalog.json"
INFLATION_DATA_PATH = DATA_DIR / "inflation.json"

# Wiki (narrative context) — root and shared schema for modules/wiki/
WIKI_DIR = BASE_DIR / "wiki"
WIKI_SCHEMA_PATH = WIKI_DIR / "SCHEMA.md"

# Wiki query module (ESJ-13): agentic tool-use chat over a single FIBRA's wiki
WIKI_QUERY_MODEL = "claude-haiku-4-5"
WIKI_QUERY_MAX_TOKENS = 4096
WIKI_QUERY_MAX_TOOL_ITERATIONS = 10
WIKI_QUERY_MAX_TOOL_RESULT_CHARS = 20000

# yfinance adds suffix .MX for BMV
TICKER_SUFFIX = ".MX"

PAGE_ICON = "ui/assets/fibralens_logo_light_v2.svg"
PAGE_TITLE = "FIBRALens"
PAGE_LEGEND = "Tu herramienta de análisis para FIBRAs mexicanas"

# Withholding tax rate for fiscal result income in Mexico
FISCAL_RESULT_WITHHOLDING_RATE = 0.30
