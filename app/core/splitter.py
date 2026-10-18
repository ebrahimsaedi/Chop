"""
Core splitting logic for Chop.

Pure Python — no Qt, no UI. Fully testable with pytest.

Design goals:
  * Preserve *all* characters: sum(parts) == text
  * Break at natural boundaries: paragraph (\n\n) → line (\n) → word ( ) → char
  * Each part roughly equal size (within `window` chars of the ideal target)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .reader import read_text

_ALREADY_SPLIT_RE = re.compile(r"_\d+$")


@dataclass(frozen=True)
class SplitResult:
    """Outcome of splitting one file."""
    source: Path
    parts: list[Path]
    encoding: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def split_text(text: str, num_parts: int, window: int = 500) -> list[str]:
    """
    Split `text` into `num_parts` roughly equal parts.

    Strategy:
      * Compute ideal split positions i * len(text) / num_parts
      * Search a small `window` around each ideal position for the closest
        natural break (paragraph, then line, then space)
      * Guarantee each part has >= 1 char and no characters are lost

    Args:
        text:       the input string
        num_parts:  how many parts to produce (>= 1)
        window:     max chars to search around each ideal split point

    Returns:
        list of `num_parts` strings whose concatenation equals `text`.

    Raises:
        ValueError: if num_parts < 1, or text is too short to split.
    """
    if num_parts < 1:
        raise ValueError(f"num_parts must be >= 1, got {num_parts}")

    total = len(text)
    if total == 0:
        return []
    if num_parts == 1:
        return [text]
    if total < num_parts:
        raise ValueError(
            f"Cannot split {total}-char text into {num_parts} parts "
            f"(need at least {num_parts} chars)."
        )

    # Never search farther than half the ideal part size — otherwise the
    # search zones of adjacent splits could overlap.
    part_size = total / num_parts
    window = max(1, min(window, int(part_size / 2) - 1))

    parts: list[str] = []
    start = 0
    for i in range(1, num_parts):
        target = i * total // num_parts   # ideal split position
        lo = start + 1                    # part must be non-empty
        hi = total - (num_parts - i)      # leave >= 1 char per remaining part

        search_lo = max(lo, target - window)
        search_hi = min(hi, target + window)

        if search_lo > search_hi:
            # Degenerate case — just split at the ideal position.
            end = max(lo, min(target, hi))
        else:
            end = _find_break(text, target, search_lo, search_hi)

        # Defensive clamp (also protects against future _find_break bugs).
        end = max(start + 1, min(end, hi))
        parts.append(text[start:end])
        start = end

    parts.append(text[start:])
    return parts


def split_file(
    source: str | Path,
    num_parts: int,
    out_dir: str | Path | None = None,
) -> SplitResult:
    """
    Split one text file into `num_parts` files named "<stem>_<i>.txt".

    Args:
        source:    path to the input .txt file
        num_parts: how many pieces
        out_dir:   destination folder (default: same as source's folder)

    Returns:
        SplitResult with the list of written file paths.

    Raises:
        FileNotFoundError: source file missing.
        ValueError:         source looks like an already-split file,
                            or it's empty / too small.
        ReadError:          (from reader) unable to decode the file.
    """
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {src}")

    if _ALREADY_SPLIT_RE.search(src.stem):
        raise ValueError(
            f"'{src.name}' looks like an already-split file "
            f"(name ends in _<number>). Rename it to split it again."
        )

    text, encoding = read_text(src)
    if not text:
        raise ValueError(f"File is empty: {src.name}")

    parts_text = split_text(text, num_parts)

    out = Path(out_dir) if out_dir is not None else src.parent
    out.mkdir(parents=True, exist_ok=True)

    suffix = src.suffix or ".txt"
    written: list[Path] = []
    for i, part in enumerate(parts_text, start=1):
        dst = out / f"{src.stem}_{i}{suffix}"
        dst.write_text(part, encoding="utf-8")   # always UTF-8, no BOM
        written.append(dst)

    return SplitResult(source=src, parts=written, encoding=encoding)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _find_break(text: str, target: int, lo: int, hi: int) -> int:
    """
    Find the natural break point in text[lo:hi] closest to `target`.

    Returns a split index `p` (exclusive end of the first part) such that
    `lo <= p <= hi`. Tries `\\n\\n` first, then `\\n`, then ` `.
    Falls back to `target` (clamped) if no natural break exists.
    """
    for sep in ("\n\n", "\n", " "):
        sep_len = len(sep)
        # We need p = found + sep_len <= hi, so found <= hi - sep_len
        idx_max = min(len(text) - sep_len, hi - sep_len)
        if idx_max < lo - sep_len:
            continue

        idx = max(0, lo - sep_len)
        best_p = -1
        best_dist = None
        while idx <= idx_max:
            found = text.find(sep, idx, idx_max + sep_len)
            if found == -1:
                break
            p = found + sep_len
            if p < lo:
                idx = found + 1
                continue
            dist = abs(p - target)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_p = p
            idx = found + 1

        if best_p != -1:
            return best_p

    # No natural break anywhere — fall back to the closest allowed point.
    return max(lo, min(target, hi))
