import json

from config import INFLATION_DATA_PATH
from modules.common.models import InflationRecord
from modules.common.repositories.base import BaseInflationReadRepository


class JsonInflationReadRepository(BaseInflationReadRepository):
    """Reads annual inflation data from the local inflation.json file."""

    def retrieve_data(self) -> list[InflationRecord]:
        """Load and parse all annual inflation records from inflation.json.

        Returns:
            list[InflationRecord]: All inflation entries parsed from the JSON file.

        Raises:
            FileNotFoundError: If inflation.json does not exist at the configured path.
        """
        if not INFLATION_DATA_PATH.exists():
            raise FileNotFoundError(f"Inflation data file not found: {INFLATION_DATA_PATH}")
        with open(INFLATION_DATA_PATH) as f:
            data = json.load(f)
        return [InflationRecord(**item) for item in data["inflation"]]
