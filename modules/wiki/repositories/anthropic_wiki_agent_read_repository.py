import logging
from collections.abc import Iterator

import anthropic

from modules.wiki.exceptions import WikiAgentError
from modules.wiki.exceptions import WikiAuthError
from modules.wiki.exceptions import WikiConnectionError
from modules.wiki.exceptions import WikiRateLimitError
from modules.wiki.models import WikiAgentEvent
from modules.wiki.models import WikiAgentEventType
from modules.wiki.models import WikiToolUse
from modules.wiki.repositories.base import BaseWikiAgentReadRepository


logger = logging.getLogger(__name__)


class AnthropicWikiAgentReadRepository(BaseWikiAgentReadRepository):
    """Runs one Anthropic Messages API turn, isolating every anthropic dependency."""

    def retrieve_data(
        self,
        system: str | list[dict],
        messages: list[dict],
        tools: list[dict],
        model: str,
        max_tokens: int,
    ) -> Iterator[WikiAgentEvent]:
        """Stream a single Anthropic Messages API turn and normalize its events.

        Builds the ``anthropic.Anthropic()`` client lazily inside this method (never
        at module/class level) and reads it inside a ``with client.messages.stream(
        ...) as stream:`` block so the underlying HTTP connection is released if the
        caller abandons this generator mid-turn (e.g. a Streamlit rerun).

        Args:
            system: System prompt for this turn — plain text, or a list of
                Anthropic content-block dicts (e.g. with a ``cache_control``
                breakpoint), forwarded to ``client.messages.stream`` unchanged.
            messages: Conversation so far, as Anthropic message dicts.
            tools: Tool schemas available to the model this turn, as Anthropic tool
                dicts.
            model: Anthropic model identifier to invoke (e.g. "claude-haiku-4-5").
            max_tokens: Maximum tokens the model may generate this turn.

        Returns:
            Iterator[WikiAgentEvent]: One TEXT_DELTA event per incremental text
                chunk, followed by exactly one TURN_COMPLETE event carrying
                stop_reason, the full turn text, any tool_uses, request_id and
                usage.

        Raises:
            WikiAuthError: If ANTHROPIC_API_KEY is missing, or the API rejects it.
            WikiRateLimitError: If the Anthropic rate limit or quota is exceeded.
            WikiConnectionError: If the Anthropic API is unreachable or the request
                times out.
            WikiAgentError: For any other Anthropic API failure.
        """
        client = anthropic.Anthropic()
        if not client.api_key:
            raise WikiAuthError("ANTHROPIC_API_KEY is not set")

        try:
            with client.messages.stream(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
                tools=tools,
            ) as stream:
                for event in stream:
                    if event.type == "text":
                        yield WikiAgentEvent(type=WikiAgentEventType.TEXT_DELTA, text=event.text)
                final_message = stream.get_final_message()
                request_id = stream.request_id
        except anthropic.AuthenticationError as exc:
            raise WikiAuthError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            raise WikiRateLimitError(str(exc)) from exc
        except (anthropic.APIConnectionError, anthropic.APITimeoutError) as exc:
            raise WikiConnectionError(str(exc)) from exc
        except anthropic.AnthropicError as exc:
            raise WikiAgentError(str(exc)) from exc

        usage = final_message.usage
        logger.info(
            "wiki agent turn complete request_id=%s input_tokens=%s output_tokens=%s cache_read_input_tokens=%s",
            request_id,
            usage.input_tokens,
            usage.output_tokens,
            usage.cache_read_input_tokens,
        )

        text = "".join(block.text for block in final_message.content if block.type == "text")
        tool_uses = [
            WikiToolUse(id=block.id, name=block.name, input=block.input)
            for block in final_message.content
            if block.type == "tool_use"
        ]
        yield WikiAgentEvent(
            type=WikiAgentEventType.TURN_COMPLETE,
            text=text,
            stop_reason=final_message.stop_reason,
            tool_uses=tool_uses,
            request_id=request_id,
            usage={
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_input_tokens": usage.cache_read_input_tokens or 0,
            },
        )
