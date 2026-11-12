"""
tests/test_prompts.py — Unit tests for prompts.py
"""

import pytest
from prompts import build_prompt, SECTION_LABELS


class TestBuildPrompt:
    """Tests for the build_prompt() function."""

    def test_returns_string(self):
        result = build_prompt("photosynthesis", "beginner")
        assert isinstance(result, str)

    def test_contains_topic(self):
        result = build_prompt("machine learning", "beginner")
        assert "machine learning" in result

    def test_contains_level_audience_beginner(self):
        result = build_prompt("gravity", "beginner")
        assert "beginner" in result.lower()

    def test_contains_level_audience_intermediate(self):
        result = build_prompt("gravity", "intermediate")
        # The intermediate description uses "basic familiarity" (not the word "intermediate")
        assert "basic familiarity" in result.lower() or "intermediate" in result.lower()

    def test_contains_level_audience_expert(self):
        result = build_prompt("gravity", "expert")
        assert "expert" in result.lower()

    def test_contains_all_section_labels(self):
        result = build_prompt("DNA replication", "beginner")
        for label in SECTION_LABELS:
            assert label in result, f"Section label '{label}' missing from prompt"

    def test_prompt_does_not_end_with_bare_heading(self):
        # The prompt's last non-empty line must NOT consist solely of a section
        # heading (e.g. "1. Simplified Explanation:").  A heading embedded inside
        # a longer instruction sentence is fine.
        result = build_prompt("photosynthesis", "beginner")
        last_line = result.rstrip().splitlines()[-1].strip()
        import re as _re
        from prompts import SECTION_LABELS as _SL
        escaped = [_re.escape(lbl) for lbl in _SL]
        bare_heading_re = _re.compile(
            r"^\*{0,2}(?:#{1,3}\s*)?(?:\d+\.\s*)?(" + "|".join(escaped) + r")\*{0,2}\s*:?\s*$",
            _re.IGNORECASE,
        )
        assert not bare_heading_re.match(last_line), (
            f"Prompt's last line is a bare section heading: {last_line!r}. "
            "This causes section 1 to be empty in Granite output."
        )

    def test_prompt_contains_section_count_constraint(self):
        # Prompt must mention all 7 sections to constrain Granite's output length
        result = build_prompt("gravity", "beginner")
        # Each section number 1-7 should appear with its label
        for i, label in enumerate(SECTION_LABELS, start=1):
            assert str(i) in result and label in result

    def test_level_case_insensitive(self):
        # Should not raise — level matching should be case-insensitive
        result = build_prompt("Newton's laws", "Beginner")
        assert isinstance(result, str)

    def test_invalid_level_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid level"):
            build_prompt("topic", "invalid_level")

    def test_whitespace_level_is_normalised(self):
        result = build_prompt("topic", "  expert  ")
        assert isinstance(result, str)

    def test_quiz_questions_mentioned(self):
        result = build_prompt("algebra", "intermediate")
        assert "Quiz" in result or "quiz" in result
