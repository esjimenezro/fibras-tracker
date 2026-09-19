from typing import Optional

from pydantic import BaseModel

from modules.wiki.models.wiki_chat_message import WikiChatMessage


class WikiQueryRequest(BaseModel):
    """Input contract for one wiki query: an allowed FIBRA scope, one question plus history.

    Attributes:
        tickers: BMV tickers this query may read from (e.g. ["FMTY14",
            "FIBRAPL14"]), at least one. The agent rejects any tool call whose
            ticker is not in this set.
        primary_ticker: The FIBRA the answer should focus on by default, e.g.
            "FMTY14". None when the query has no single focus — a comparison
            across all of ``tickers`` on equal footing.
        question: The user's natural-language question for this turn.
        history: Prior turns for this thread, oldest first. Empty on the first turn.
    """

    tickers: list[str]
    primary_ticker: Optional[str] = None
    question: str
    history: list[WikiChatMessage] = []
