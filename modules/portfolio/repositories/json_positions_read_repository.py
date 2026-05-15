import json

from config import POSITIONS_FILE
from modules.portfolio.models.position import Position
from modules.portfolio.repositories.base.base_positions_read_repository import BasePositionsReadRepository


class JsonPositionsReadRepository(BasePositionsReadRepository):
    """Reads portfolio positions from the local positions.json file."""

    def retrieve_data(self) -> list[Position]:
        """Load and parse positions from positions.json, returning them as Position models."""
        with open(POSITIONS_FILE) as f:
            data = json.load(f)
        return [Position(**item) for item in data["positions"]]
