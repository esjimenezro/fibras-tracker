from typing import Optional

from pydantic import BaseModel

from modules.common.schemas import ServiceStatus
from modules.fundamentals.models import FundamentalsHistory


class FundamentalsDataRetrieverServiceSchema(BaseModel):
    """Output contract for FundamentalsDataRetrieverService.

    Attributes:
        status: Result status; always populated.
        data: The assembled FundamentalsHistory on success; None on error.
        error_message: Exception message on error; None on success.
    """

    status: ServiceStatus
    data: Optional[FundamentalsHistory] = None
    error_message: Optional[str] = None
