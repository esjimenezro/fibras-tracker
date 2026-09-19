import json

from config import FUNDAMENTALS_DATA_PATH
from modules.fundamentals.models import FundamentalsRecord
from modules.fundamentals.repositories.base import BaseFundamentalsReadRepository


class JsonFundamentalsReadRepository(BaseFundamentalsReadRepository):
    """Reads fundamentals records from the local fundamentals.json file."""

    def retrieve_data(self) -> list[FundamentalsRecord]:
        """Load and parse all fundamentals records from fundamentals.json.

        Returns:
            list[FundamentalsRecord]: All records parsed from the JSON file.

        Raises:
            FileNotFoundError: If fundamentals.json does not exist at the configured path.
        """
        if not FUNDAMENTALS_DATA_PATH.exists():
            raise FileNotFoundError(f"Fundamentals data file not found: {FUNDAMENTALS_DATA_PATH}")
        with open(FUNDAMENTALS_DATA_PATH) as f:
            data = json.load(f)
        return [FundamentalsRecord(**item) for item in data["fundamentals"]]
