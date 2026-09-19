import json

from config import POSITIONS_DATA_PATH
from modules.portfolio.models import Position
from modules.portfolio.repositories.base import BasePositionsReadRepository


class JsonPositionsReadRepository(BasePositionsReadRepository):
    """Reads portfolio positions from the local positions.json file."""

    def retrieve_data(self) -> list[Position]:
        """Load and parse all positions from positions.json.

        Returns:
            list[Position]: All positions parsed from the JSON file.
        """
        if not POSITIONS_DATA_PATH.exists():
            raise FileNotFoundError(f"Positions data file not found: {POSITIONS_DATA_PATH}")
        with open(POSITIONS_DATA_PATH) as f:
            data = json.load(f)
        return [Position(**item) for item in data["positions"]]
