import re


_SAFE_SLUG = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?")


def validate_wiki_slug(value: str, *, label: str) -> str:
    """Return ``value`` unchanged if it is a safe single path segment, else raise.

    A safe slug is a non-empty string of ASCII letters, digits, dots, underscores
    and hyphens that starts and ends with an alphanumeric and contains no ``..``
    sequence. This blocks path traversal (``..``, ``/``, ``\\``) before the value
    is interpolated into a filesystem path under the wiki tree.

    Args:
        value: Candidate slug, e.g. a ticker or a resolved wiki page name.
        label: Field name shown in the error message (e.g. "ticker").

    Returns:
        str: The validated value, unchanged.

    Raises:
        ValueError: If ``value`` is empty, contains a path separator or a ``..``
            sequence, or is otherwise not a safe single path segment.
    """
    if ".." in value or not _SAFE_SLUG.fullmatch(value):
        raise ValueError(f"Unsafe wiki {label} '{value}': expected a simple slug (no path separators or '..')")
    return value
