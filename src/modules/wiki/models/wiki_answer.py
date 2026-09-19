from pydantic import BaseModel


class WikiAnswer(BaseModel):
    """Raw final answer text produced by the agent for a wiki query.

    Attributes:
        answer_text: Final assistant answer as markdown, before citation extraction.
    """

    answer_text: str
