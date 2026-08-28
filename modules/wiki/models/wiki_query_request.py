from pydantic import BaseModel

from modules.wiki.models.wiki_chat_message import WikiChatMessage


class WikiQueryRequest(BaseModel):
    """Input contract for one wiki query: a single FIBRA, one question plus history.

    Attributes:
        ticker: BMV ticker of the FIBRA the question is about (e.g. "DANHOS13").
            The agent rejects any tool call whose ticker differs from this one.
        question: The user's natural-language question for this turn.
        history: Prior turns for this ticker, oldest first. Empty on the first turn.
    """

    ticker: str
    question: str
    history: list[WikiChatMessage] = []
