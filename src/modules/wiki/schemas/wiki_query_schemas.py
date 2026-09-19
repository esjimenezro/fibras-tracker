from typing import Optional

from pydantic import BaseModel

from modules.common.schemas import ServiceStatus
from modules.wiki.models import WikiQueryResponse


class WikiQueryServiceSchema(BaseModel):
    """Output contract for WikiQueryService.run().

    Attributes:
        status: Result status; always populated.
        data: The enriched WikiQueryResponse on success; None on error.
        error_message: Exception message on error; None on success.
    """

    status: ServiceStatus
    data: Optional[WikiQueryResponse] = None
    error_message: Optional[str] = None
