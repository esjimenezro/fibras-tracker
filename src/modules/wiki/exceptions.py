class WikiAgentError(Exception):
    """Base class for every error raised by the wiki query agent layer.

    The Anthropic agent port translates provider failures into this hierarchy so
    that WikiQueryService can map them to typed stream events without importing
    the ``anthropic`` package. It is also raised directly for failures that do not
    fit a more specific subclass (e.g. malformed requests).
    """


class WikiAuthError(WikiAgentError):
    """Raised when the Anthropic API rejects the credentials.

    Corresponds to a missing or invalid ``ANTHROPIC_API_KEY``.
    """


class WikiRateLimitError(WikiAgentError):
    """Raised when the Anthropic API returns a rate-limit or quota error."""


class WikiConnectionError(WikiAgentError):
    """Raised when the Anthropic API is unreachable or the request times out."""
