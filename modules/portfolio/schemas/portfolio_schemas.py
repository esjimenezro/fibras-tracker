from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from modules.portfolio.models.portfolio import Portfolio


class PortfolioDataRetrieverStatus(StrEnum):
    """Valid status values for PortfolioDataRetrieverServiceSchema.

    Attributes:
        OK: The service completed successfully and data is populated.
        ERROR: The service encountered an exception and error_message is populated.
    """

    OK = "OK"
    ERROR = "ERROR"


class PortfolioDataRetrieverServiceSchema(BaseModel):
    """Output contract for PortfolioDataRetrieverService.

    Attributes:
        status: Result status; always populated.
        data: The assembled Portfolio on success; None on error.
        error_message: Exception message on error; None on success.
    """

    status: PortfolioDataRetrieverStatus
    data: Optional[Portfolio] = None
    error_message: Optional[str] = None
