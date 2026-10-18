from __future__ import annotations

from pathlib import Path

from charset_normalizer import from_bytes


class ReadError(Exception):
    """Raised when a file cannot be read as text."""


def read_text(path: str | Path) -> tuple[str, str]:
    """
    Read a text file, auto-detecting its encoding.

    Returns:
        (text, encoding)
            text     — decoded content as str
            encoding — name of the encoding that was used

    Raises:
        ReadError: file missing, unreadable, or looks binary.

    Strategy:
        1) Try UTF-8 first (covers ASCII + most modern files, fast).
        2) If that fails, ask charset-normalizer to guess.
        3) Last resort: latin-1 (never fails, may produce mojibake).
    """
    p = Path(path)
    if not p.exists():
        raise ReadError(f"File not found: {p}")
    if not p.is_file():
        raise ReadError(f"Not a regular file: {p}")

    try:
        raw = p.read_bytes()
    except OSError as e:
        raise ReadError(f"Cannot read {p.name}: {e}") from e

    if not raw:
        return "", "utf-8"

    # ---- Fast path: UTF-8 ----
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = None

    if text is not None:
        if _looks_binary(text):
            raise ReadError(f"File looks binary, not text: {p.name}")
        return text, "utf-8"

    # ---- Slow path: charset-normalizer ----
    try:
        match = from_bytes(raw).best()
    except Exception as e:
        raise ReadError(f"Could not detect encoding of {p.name}: {e}") from e

    if match is None:
        text = raw.decode("latin-1")
        if _looks_binary(text):
            raise ReadError(f"File looks binary, not text: {p.name}")
        return text, "latin-1"

    text = str(match)  # CharsetMatch.__str__ returns decoded text
    if _looks_binary(text):
        raise ReadError(f"File looks binary, not text: {p.name}")
    return text, match.encoding


def _looks_binary(text: str) -> bool:
    """Heuristic: NUL byte = binary; many control chars = binary."""
    if not text:
        return False
    sample = text[:4096]
    if "\x00" in sample:
        return True
    bad = sum(1 for ch in sample if ord(ch) < 9 or 13 < ord(ch) < 32)
    return bad > len(sample) * 0.05
