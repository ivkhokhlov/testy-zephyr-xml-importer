from __future__ import annotations

import html
import re


# NOTE: This is intentionally minimal; the loop will evolve it.
_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_html(fragment: str | None) -> str:
    """
    Convert Zephyr HTML/CDATA fragments to deterministic plain text.

    Required behaviors (see docs/spec.md):
    - <br> -> newline
    - </p>, </div> -> newline
    - <li> -> "- " prefix; </li> -> newline
    - </tr> -> newline; </td>, </th> -> tab
    - remove remaining tags
    - html.unescape
    - normalize blank lines and trim
    """
    if not fragment:
        return ""

    s = fragment

    # Normalize common tags to placeholders/newlines/tabs
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</\s*(p|div)\s*>", "\n", s)

    # list items
    s = re.sub(r"(?i)<\s*li\s*>", "- ", s)
    s = re.sub(r"(?i)</\s*li\s*>", "\n", s)

    # tables
    s = re.sub(r"(?i)</\s*tr\s*>", "\n", s)
    s = re.sub(r"(?i)</\s*(td|th)\s*>", "\t", s)

    # Remove remaining tags
    s = _TAG_RE.sub("", s)

    # Unescape HTML entities
    s = html.unescape(s)

    # Remove some invisible unicode chars (Word joiner etc.)
    s = s.replace("\u2060", "").replace("\ufeff", "")
    s = s.replace("\xa0", " ")

    # Normalize line endings and collapse excessive blank lines
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()
