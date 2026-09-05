from abc import ABC
from abc import abstractmethod
from collections.abc import Iterator

from modules.wiki.models import WikiAgentEvent


class BaseWikiAgentReadRepository(ABC):
    """Abstract interface for running one LLM agent turn against any provider."""

    @abstractmethod
    def retrieve_data(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        model: str,
        max_tokens: int,
    ) -> Iterator[WikiAgentEvent]:
        """Run a single model turn and normalize its events.

        One invocation corresponds to exactly one model turn — looping across
        multiple turns (e.g. after a tool result) is the caller's responsibility.

        Args:
            system: System prompt for this turn.
            messages: Conversation so far, in the provider's raw message format.
            tools: Tool schemas available to the model this turn, in the
                provider's raw tool format.
            model: Model identifier to invoke.
            max_tokens: Maximum tokens the model may generate this turn.

        Returns:
            Iterator[WikiAgentEvent]: One TEXT_DELTA event per incremental text
                chunk, followed by exactly one TURN_COMPLETE event once the turn
                ends.

        Raises:
            WikiAuthError: If credentials are missing or invalid.
            WikiRateLimitError: If the provider's rate limit or quota is exceeded.
            WikiConnectionError: If the provider is unreachable or the request
                times out.
            WikiAgentError: For any other provider failure.
        """
        ...
