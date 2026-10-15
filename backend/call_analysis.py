import re


def without_key_moments(text: str) -> str:
    """Omit the retired final section from generated and saved call analyses."""
    return re.split(
        r"(?im)^[ \t]*(?:#{1,6}[ \t]+)?(?:\*\*)?5\.[ \t]+(?:Key moments|Momentos principais)\b",
        text, maxsplit=1,
    )[0].rstrip()
