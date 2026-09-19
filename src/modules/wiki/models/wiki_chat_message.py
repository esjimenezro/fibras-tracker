from typing import Literal

from pydantic import BaseModel


class WikiChatMessage(BaseModel):
    """A single turn in a wiki chat conversation, as kept in session history.

    Attributes:
        role: Who produced the turn — "user" for a question, "assistant" for an answer.
        content: Plain-text content of the turn (history is collapsed to text; a turn
            never carries tool-call structure).
    """

    role: Literal["user", "assistant"]
    content: str
