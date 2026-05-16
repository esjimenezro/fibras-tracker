import json

from config import DISTRIBUTIONS_FILE
from modules.portfolio.models.distribution import Distribution
from modules.portfolio.repositories.base.base_distributions_read_repository import BaseDistributionsReadRepository


class JsonDistributionsReadRepository(BaseDistributionsReadRepository):
    """Reads distribution records from the local distributions.json file."""

    def retrieve_data(self) -> list[Distribution]:
        """Load and parse all distribution records from distributions.json.

        Returns:
            list[Distribution]: All distribution records parsed from the JSON file.
        """
        with open(DISTRIBUTIONS_FILE) as f:
            data = json.load(f)
        return [Distribution(**item) for item in data["distributions"]]
