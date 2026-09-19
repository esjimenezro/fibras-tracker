from typing import Optional

from pydantic import BaseModel

from modules.common.schemas import ServiceStatus


class WikiCatalogServiceSchema(BaseModel):
    """Output contract for WikiCatalogService.

    Attributes:
        status: Result status; always populated.
        data: BMV tickers of the FIBRAs that have a wiki, sorted, on success;
            None on error.
        error_message: Exception message on error; None on success.
    """

    status: ServiceStatus
    data: Optional[list[str]] = None
    error_message: Optional[str] = None
