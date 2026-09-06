from config import WIKI_QUERY_MAX_TOOL_RESULT_CHARS
from modules.wiki.models import WikiAgentEvent
from modules.wiki.models import WikiQueryRequest


_TRUNCATION_MARKER = "\n… [contenido truncado]"


class WikiMessageProcessor:
    """Builds the Anthropic message/content dicts a wiki query turn needs.

    Transformation: domain objects (WikiQueryRequest, WikiAgentEvent, raw tool
    payloads) → Anthropic Messages API dicts. Pure: no repositories, no I/O; the
    only external value is the tool-result size cap from config.
    """

    def initial_messages(self, request: WikiQueryRequest) -> list[dict]:
        """Build the starting message list: collapsed history pairs + the question.

        History is collapsed to plain text, all-or-nothing per (user, assistant)
        pair — a dangling or non-alternating turn is dropped so no tool_use block
        is ever left orphaned.

        Args:
            request: The wiki query carrying prior turns in ``history``.

        Returns:
            list[dict]: Anthropic message dicts, ending with the new user question.
        """
        messages: list[dict] = []
        history = request.history
        for user_msg, assistant_msg in zip(history[::2], history[1::2]):
            if user_msg.role == "user" and assistant_msg.role == "assistant":
                messages.append({"role": "user", "content": user_msg.content})
                messages.append({"role": "assistant", "content": assistant_msg.content})
        messages.append({"role": "user", "content": request.question})
        return messages

    def assistant_content(self, turn: WikiAgentEvent) -> list[dict]:
        """Rebuild an assistant turn's content blocks (text + tool_use) for replay.

        Args:
            turn: A TURN_COMPLETE event whose stop_reason was "tool_use".

        Returns:
            list[dict]: An optional text block followed by one tool_use block per
                requested tool call, ids preserved so tool_result blocks match.
        """
        content: list[dict] = []
        if turn.text:
            content.append({"type": "text", "text": turn.text})
        for tool_use in turn.tool_uses:
            content.append({
                "type": "tool_use",
                "id": tool_use.id,
                "name": tool_use.name,
                "input": tool_use.input,
            })
        return content

    def tool_result(self, tool_use_id: str, content: str, is_error: bool) -> dict:
        """Build a tool_result block, capping content at the configured size.

        Args:
            tool_use_id: Id of the tool_use block this result answers.
            content: The tool payload text.
            is_error: Whether this result reports a failed tool call.

        Returns:
            dict: The tool_result block, content capped at
                WIKI_QUERY_MAX_TOOL_RESULT_CHARS with a marker when truncated.
        """
        if len(content) > WIKI_QUERY_MAX_TOOL_RESULT_CHARS:
            content = content[:WIKI_QUERY_MAX_TOOL_RESULT_CHARS] + _TRUNCATION_MARKER
        return {
            "type": "tool_result",
            "tool_use_id": tool_use_id,
            "content": content,
            "is_error": is_error,
        }
