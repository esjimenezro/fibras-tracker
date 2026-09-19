from typing import Optional

from pydantic import BaseModel

from modules.common.schemas import ServiceStatus
from modules.portfolio.models import Portfolio


class PortfolioDataRetrieverServiceSchema(BaseModel):
    """Output contract for PortfolioDataRetrieverService.

    Attributes:
        status: Result status; always populated.
        data: The assembled Portfolio on success; None on error.
        error_message: Exception message on error; None on success.
    """

    status: ServiceStatus
    data: Optional[Portfolio] = None
    error_message: Optional[str] = None
