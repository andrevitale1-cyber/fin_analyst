import re


def without_key_moments(text: str) -> str:
    """Omit the retired final section and agent file notices from generated and saved call analyses."""
    # The hosted agent sometimes reports a sandbox file ("Saved the analysis to [x.md](/workspace/...)"); users must not see it.
    text = re.sub(r"(?im)^[ \t]*(?:Saved|Salv[ao]|Salvei)\b[^\n]*\]\((?:sandbox:)?/(?:workspace|mnt)/[^)]*\)[^\n]*\n*", "", text)
    return re.split(
        r"(?im)^[ \t]*(?:#{1,6}[ \t]+)?(?:\*\*)?5\.[ \t]+(?:Key moments|Momentos principais)\b",
        text, maxsplit=1,
    )[0].rstrip()
