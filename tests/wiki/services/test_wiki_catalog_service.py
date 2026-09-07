from modules.common.schemas import ServiceStatus
from modules.wiki.repositories import FileSystemWikiCatalogReadRepository
from modules.wiki.services import WikiCatalogService


# --- Catalog repository stand-ins ------------------------------------------

class _StubCatalogRepository:
    """Catalog repository stand-in returning scripted lower-case slugs."""

    def __init__(self, tickers):
        """Store the slugs to return."""
        self._tickers = tickers

    def retrieve_data(self):
        """Return the scripted slugs."""
        return list(self._tickers)


class _RaisingCatalogRepository:
    """Catalog repository stand-in that fails on read."""

    def retrieve_data(self):
        """Raise to exercise the service's error branch."""
        raise OSError("no se pudo leer wiki/")


# --- Success path ----------------------------------------------------------

def test_run_uppercases_committed_wiki_tickers():
    """The real repository's lower-case slugs come back as BMV tickers."""
    service = WikiCatalogService(catalog_repository=FileSystemWikiCatalogReadRepository())

    result = service.run()

    assert result.status == ServiceStatus.OK
    assert result.data == ["DANHOS13", "FMTY14"]
    assert result.error_message is None


def test_run_with_empty_catalog_is_ok_not_error():
    """An empty catalog is a successful, empty result."""
    service = WikiCatalogService(catalog_repository=_StubCatalogRepository(tickers=[]))

    result = service.run()

    assert result.status == ServiceStatus.OK
    assert result.data == []


# --- Error path ------------------------------------------------------------

def test_run_returns_error_when_repository_raises():
    """A repository failure becomes status=ERROR carrying the exception message."""
    service = WikiCatalogService(catalog_repository=_RaisingCatalogRepository())

    result = service.run()

    assert result.status == ServiceStatus.ERROR
    assert result.data is None
    assert "no se pudo leer wiki/" in result.error_message
