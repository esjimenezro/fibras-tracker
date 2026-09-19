from typing import Optional

from modules.common.schemas import ServiceStatus
from modules.wiki.repositories.base import BaseWikiCatalogReadRepository
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository
from modules.wiki.schemas import WikiCatalogServiceSchema


class WikiCatalogService:
    """Reports which FIBRAs have a wiki, as BMV tickers callers can match directly."""

    def __init__(
        self,
        catalog_repository: Optional[BaseWikiCatalogReadRepository] = None,
    ) -> None:
        """Initialise the repository.

        Args:
            catalog_repository: Repository listing the wiki ticker slugs.
                Defaults to FileSystemWikiCatalogReadRepository.
        """
        self._catalog_repository = catalog_repository or FileSystemWikiCatalogReadRepository()

    def run(self) -> WikiCatalogServiceSchema:
        """List the FIBRAs that have a wiki, upper-cased to BMV ticker form.

        The repository yields lower-case directory slugs ("danhos13"); this
        service normalises them so callers compare against the BMV tickers used
        everywhere else ("DANHOS13") without knowing the on-disk layout.

        Returns:
            WikiCatalogServiceSchema: status=OK with the sorted BMV tickers on
                success, or status=ERROR with the exception message on failure.
        """
        try:

            slugs = self._catalog_repository.retrieve_data()

            return WikiCatalogServiceSchema(
                status=ServiceStatus.OK,
                data=[slug.upper() for slug in slugs],
            )

        except Exception as e:

            return WikiCatalogServiceSchema(
                status=ServiceStatus.ERROR,
                error_message=str(e),
            )
