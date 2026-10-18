"""Tests for app.core.splitter — pure logic, no Qt."""

from __future__ import annotations

import pytest

from app.core.splitter import split_text, split_file


# ---------------------------------------------------------------------------
# split_text — invariants
# ---------------------------------------------------------------------------

def test_one_part_returns_whole_text():
    assert split_text("hello world", 1) == ["hello world"]


def test_empty_text_returns_empty_list():
    assert split_text("", 3) == []


def test_num_parts_must_be_positive():
    with pytest.raises(ValueError):
        split_text("abc", 0)
    with pytest.raises(ValueError):
        split_text("abc", -1)


def test_text_too_small_raises():
    with pytest.raises(ValueError):
        split_text("abc", 5)


@pytest.mark.parametrize("n", [2, 3, 4, 5, 7])
def test_characters_are_preserved(n):
    text = "A " * 500 + "\n\n" + "B " * 300 + "\n" + "C " * 200
    parts = split_text(text, n)
    assert len(parts) == n
    assert "".join(parts) == text
    assert all(len(p) > 0 for p in parts)


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_parts_are_roughly_equal(n):
    text = ("word " * 1000).strip()
    parts = split_text(text, n)
    ideal = len(text) / n
    for p in parts:
        # Each part should be within 5% of ideal (generous, natural breaks)
        assert abs(len(p) - ideal) <= ideal * 0.05, [len(p) for p in parts]


# ---------------------------------------------------------------------------
# split_text — break preference
# ---------------------------------------------------------------------------

def test_prefers_paragraph_breaks():
    para = "x" * 200
    text = para + "\n\n" + para + "\n\n" + para
    parts = split_text(text, 2)
    # The first part should end exactly after a paragraph break
    assert parts[0].endswith("x" * 200 + "\n\n") or parts[0] == para + "\n\n"


def test_falls_back_to_lines_when_no_paragraphs():
    line = "y" * 100
    text = "\n".join([line] * 6)  # 6 lines, no blank lines
    parts = split_text(text, 3)
    assert "".join(parts) == text
    for p in parts:
        # Each part should end with a newline (or be the last part)
        assert p.endswith("\n") or p is parts[-1]


def test_falls_back_to_words_when_no_newlines():
    text = ("alpha beta gamma delta " * 100).strip()
    parts = split_text(text, 3)
    assert "".join(parts) == text
    # No part should end mid-word (except possibly the last)
    for p in parts[:-1]:
        assert not p.endswith(("a", "b", "c", "d", "e")) or p.endswith(" ")


def test_handles_text_with_no_natural_breaks():
    text = "a" * 10000  # one giant word
    parts = split_text(text, 4)
    assert "".join(parts) == text
    assert len(parts) == 4


# ---------------------------------------------------------------------------
# split_text — unicode / farsi
# ---------------------------------------------------------------------------

def test_farsi_text():
    text = ("این یک جمله‌ی آزمایشی است. " * 100).strip()
    parts = split_text(text, 3)
    assert "".join(parts) == text
    # No part starts or ends with half a combining character
    for p in parts:
        assert not p.endswith("\u200c") or p.endswith(" ")  # ZWNJ ok only if before space


def test_emoji_preserved():
    text = "😀 hello 🌍 " * 200
    parts = split_text(text, 4)
    assert "".join(parts) == text


# ---------------------------------------------------------------------------
# split_file — filesystem
# ---------------------------------------------------------------------------

def test_split_file_creates_expected_files(tmp_path):
    src = tmp_path / "book.txt"
    src.write_text(("Sentence one. Sentence two. " * 100).strip(), encoding="utf-8")

    result = split_file(src, 3)

    assert result.source == src
    assert result.encoding == "utf-8"
    assert len(result.parts) == 3
    for i, p in enumerate(result.parts, start=1):
        assert p.name == f"book_{i}.txt"
        assert p.exists()
        assert p.read_text(encoding="utf-8")  # readable

    combined = "".join(p.read_text(encoding="utf-8") for p in result.parts)
    assert combined == src.read_text(encoding="utf-8")


def test_split_file_rejects_already_split(tmp_path):
    src = tmp_path / "book_2.txt"
    src.write_text("hello world", encoding="utf-8")
    with pytest.raises(ValueError, match="already-split"):
        split_file(src, 2)


def test_split_file_rejects_empty(tmp_path):
    src = tmp_path / "empty.txt"
    src.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        split_file(src, 2)


def test_split_file_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        split_file(tmp_path / "nope.txt", 2)


def test_split_file_writes_utf8(tmp_path):
    src = tmp_path / "farsi.txt"
    src.write_text("سلام دنیا. " * 50, encoding="utf-8")
    result = split_file(src, 2)
    for p in result.parts:
        raw = p.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf")  # no BOM
        raw.decode("utf-8")  # must be valid UTF-8
