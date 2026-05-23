import json

from config import CATALOG_DATA_PATH
from modules.common.models import Fibra
from modules.common.repositories.base import BaseCatalogReadRepository


class JsonCatalogReadRepository(BaseCatalogReadRepository):
    """Reads the FIBRA catalog from the local catalog.json file."""

    def retrieve_data(self) -> list[Fibra]:
        """Load and parse all FIBRA entries from catalog.json.

        Returns:
            list[Fibra]: All FIBRA catalog entries parsed from the JSON file.

        Raises:
            FileNotFoundError: If catalog.json does not exist at the configured path.
        """
        if not CATALOG_DATA_PATH.exists():
            raise FileNotFoundError(f"Catalog data file not found: {CATALOG_DATA_PATH}")
        with open(CATALOG_DATA_PATH) as f:
            data = json.load(f)
        return [Fibra(**item) for item in data["fibras"]]
