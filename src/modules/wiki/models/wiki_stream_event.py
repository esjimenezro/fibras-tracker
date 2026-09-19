from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from modules.wiki.models.wiki_query_response import WikiQueryResponse


class WikiStreamEventType(StrEnum):
    """Type of event surfaced by WikiQueryService.stream() to the UI.

    Attributes:
        TEXT: An incremental chunk of the answer being streamed.
        STATUS: A human-readable progress note (e.g. "Consultando la wiki…").
        FINAL: Terminal success event; carries the enriched WikiQueryResponse.
        ERROR: Terminal failure event; carries error_category and error_message.
    """

    TEXT = "TEXT"
    STATUS = "STATUS"
    FINAL = "FINAL"
    ERROR = "ERROR"


class WikiErrorCategory(StrEnum):
    """Category of a terminal ERROR stream event, used to pick the UI banner.

    Attributes:
        AUTH: Missing or invalid Anthropic API key.
        RATE_LIMIT: Anthropic rate limit or quota exceeded.
        CONNECTION: Anthropic API unreachable or the request timed out.
        INTERNAL: Any other unexpected failure in the pipeline.
        INCOMPLETE: The tool-iteration cap was reached before a final answer.
    """

    AUTH = "AUTH"
    RATE_LIMIT = "RATE_LIMIT"
    CONNECTION = "CONNECTION"
    INTERNAL = "INTERNAL"
    INCOMPLETE = "INCOMPLETE"


class WikiStreamEvent(BaseModel):
    """A single event in the stream returned by WikiQueryService.stream().

    Exactly one terminal event (FINAL or ERROR) is emitted per query, always last.

    Attributes:
        type: Which kind of event this is.
        text: For TEXT, the incremental answer chunk; for STATUS, the progress note.
            None for FINAL and ERROR.
        data: The enriched answer on FINAL; None otherwise.
        error_category: Failure category on ERROR; None otherwise.
        error_message: Human-readable failure detail on ERROR; None otherwise.
    """

    type: WikiStreamEventType
    text: Optional[str] = None
    data: Optional[WikiQueryResponse] = None
    error_category: Optional[WikiErrorCategory] = None
    error_message: Optional[str] = None
