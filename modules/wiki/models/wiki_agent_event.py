from enum import StrEnum
from typing import Optional

from pydantic import BaseModel


class WikiAgentEventType(StrEnum):
    """Type of event emitted by the Anthropic agent port for one model turn.

    Attributes:
        TEXT_DELTA: An incremental chunk of assistant text within the current turn.
        TURN_COMPLETE: The turn finished; carries stop reason, full turn text, tool
            uses, request id and token usage.
    """

    TEXT_DELTA = "TEXT_DELTA"
    TURN_COMPLETE = "TURN_COMPLETE"


class WikiToolUse(BaseModel):
    """A single tool call requested by the model in a completed turn.

    Attributes:
        id: Anthropic tool-use block id, echoed back on the matching tool result.
        name: Tool requested (e.g. "read_index", "read_page", "read_fundamentals").
        input: Raw tool input arguments as provided by the model.
    """

    id: str
    name: str
    input: dict


class WikiAgentEvent(BaseModel):
    """A normalized event from a single model turn, free of any ``anthropic`` types.

    Attributes:
        type: Which kind of event this is.
        text: For TEXT_DELTA, the incremental text chunk; for TURN_COMPLETE, the full
            assistant text of the turn. None when not applicable.
        stop_reason: Model stop reason on TURN_COMPLETE (e.g. "end_turn", "tool_use").
            None on TEXT_DELTA.
        tool_uses: Tool calls requested in the turn; empty list when none.
        request_id: Anthropic request id for the turn, for logging. None until known.
        usage: Token usage for the turn keyed by name (e.g. "input_tokens",
            "output_tokens", "cache_read_input_tokens"). None until known.
    """

    type: WikiAgentEventType
    text: Optional[str] = None
    stop_reason: Optional[str] = None
    tool_uses: list[WikiToolUse] = []
    request_id: Optional[str] = None
    usage: Optional[dict[str, int]] = None
