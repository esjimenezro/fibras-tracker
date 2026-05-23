import json

from config import DISTRIBUTIONS_DATA_PATH
from modules.portfolio.models import Distribution
from modules.portfolio.repositories.base import BaseDistributionsReadRepository


class JsonDistributionsReadRepository(BaseDistributionsReadRepository):
    """Reads distribution records from the local distributions.json file."""

    def retrieve_data(self) -> list[Distribution]:
        """Load and parse all distribution records from distributions.json.

        Returns:
            list[Distribution]: All distribution records parsed from the JSON file.
        """
        if not DISTRIBUTIONS_DATA_PATH.exists():
            raise FileNotFoundError(f"Distributions data file not found: {DISTRIBUTIONS_DATA_PATH}")
        with open(DISTRIBUTIONS_DATA_PATH) as f:
            data = json.load(f)
        return [Distribution(**item) for item in data["distributions"]]
