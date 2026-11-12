"""
tests/test_app.py — Integration tests for Flask routes in app.py

All IBM watsonx.ai calls are mocked — no real API calls are made.
"""

import pytest
from unittest.mock import patch


@pytest.fixture
def client():
    """Create a Flask test client with testing mode enabled."""
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ── GET / ────────────────────────────────────────────────────────────────────

class TestIndexRoute:

    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_returns_html(self, client):
        response = client.get("/")
        assert b"EduSimplify" in response.data
        assert b"<html" in response.data.lower()


# ── POST /simplify — Input Validation ────────────────────────────────────────

class TestSimplifyValidation:

    def test_missing_body_returns_400(self, client):
        response = client.post("/simplify", content_type="application/json", data="")
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_empty_topic_returns_400(self, client):
        payload = {"topic": "   ", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "topic" in data["error"].lower()

    def test_missing_topic_key_returns_400(self, client):
        payload = {"level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_invalid_level_returns_400(self, client):
        payload = {"topic": "photosynthesis", "level": "master"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False

    def test_missing_level_key_returns_400(self, client):
        payload = {"topic": "photosynthesis"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 400

    def test_topic_too_long_returns_400(self, client):
        payload = {"topic": "x" * 2001, "level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False


# ── Realistic Granite output samples ─────────────────────────────────────────
# These mirror what Granite-4-h-small actually produces in practice.

# Style A: numbered headings with colon (most common)
MOCK_NUMBERED_COLON = """\
1. Simplified Explanation:
Photosynthesis is how plants make food using sunlight, water, and CO2.

2. Key Concepts:
- Chlorophyll absorbs sunlight
- CO2 and water are raw materials
- Glucose and oxygen are products

3. Real-world Analogy:
It is like a solar panel that converts sunlight into usable energy.

4. Example:
A leaf exposed to sunlight produces glucose and releases oxygen.

5. Important Terms:
- Chlorophyll: the green pigment that captures light
- Glucose: sugar produced as food for the plant
- Photosynthesis: the process of making food from light

6. Quick Revision:
- Plants need sunlight, CO2, and water
- Chlorophyll captures light energy
- Products are glucose and oxygen

7. Quiz Questions:
Q1. What is the main product of photosynthesis?
A) Oxygen  B) Glucose  C) Carbon dioxide  D) Water
Answer: B
Q2. Which pigment captures sunlight?
A) Melanin  B) Carotene  C) Chlorophyll  D) Hemoglobin
Answer: C
Q3. Where does photosynthesis mainly occur?
A) Roots  B) Stem  C) Leaves  D) Flowers
Answer: C
"""

# Style B: numbered headings WITHOUT colon
MOCK_NUMBERED_NO_COLON = """\
1. Simplified Explanation
Photosynthesis is how plants make their own food.

2. Key Concepts
- Light energy is converted to chemical energy
- Carbon dioxide is absorbed from air

3. Real-world Analogy
Like cooking — you take raw ingredients and energy to make food.

4. Example
A houseplant sitting near a window performing photosynthesis daily.

5. Important Terms
- ATP: energy currency of the cell

6. Quick Revision
- Requires light, CO2, water
- Produces glucose and oxygen

7. Quiz Questions
Q1. What gas is released during photosynthesis?
A) CO2  B) Nitrogen  C) Oxygen  D) Hydrogen
Answer: C
"""

# Style C: Markdown bold headings (**Heading:**)
MOCK_MARKDOWN_BOLD = """\
**Simplified Explanation:**
Plants use sunlight to make food in a process called photosynthesis.

**Key Concepts:**
- Light is the energy source
- Chlorophyll is the key pigment

**Real-world Analogy:**
Like solar panels turning sunlight into electricity.

**Example:**
A green leaf making glucose on a sunny day.

**Important Terms:**
- Glucose: simple sugar
- Oxygen: byproduct released

**Quick Revision:**
- Inputs: light, CO2, water
- Outputs: glucose, oxygen

**Quiz Questions:**
Q1. What colour is chlorophyll?
A) Red  B) Blue  C) Green  D) Yellow
Answer: C
"""

# Style D: Markdown ATX headings (## Heading)
MOCK_MARKDOWN_ATX = """\
## Simplified Explanation
Plants capture light energy to convert CO2 and water into glucose.

## Key Concepts
- Photosynthesis occurs in chloroplasts

## Real-world Analogy
A factory that uses solar power to manufacture sugar.

## Example
Aquatic plants releasing oxygen bubbles in sunlight.

## Important Terms
- Chloroplast: organelle where photosynthesis occurs

## Quick Revision
- Light drives the reaction
- Oxygen is a byproduct

## Quiz Questions
Q1. In which organelle does photosynthesis occur?
A) Nucleus  B) Mitochondria  C) Chloroplast  D) Ribosome
Answer: C
"""


# ── POST /simplify — Successful Mocked Response ───────────────────────────────

class TestSimplifySuccess:

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_successful_response_returns_200(self, mock_gen, client):
        payload = {"topic": "photosynthesis", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 200

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_successful_response_has_success_true(self, mock_gen, client):
        payload = {"topic": "photosynthesis", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        data = response.get_json()
        assert data["success"] is True

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_successful_response_has_sections(self, mock_gen, client):
        payload = {"topic": "photosynthesis", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        data = response.get_json()
        assert "sections" in data
        assert isinstance(data["sections"], dict)

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_sections_contain_expected_keys(self, mock_gen, client):
        payload = {"topic": "photosynthesis", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        data = response.get_json()
        sections = data["sections"]
        assert "Simplified Explanation" in sections
        assert "Quiz Questions" in sections

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_simplified_explanation_has_content(self, mock_gen, client):
        payload = {"topic": "photosynthesis", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        data = response.get_json()
        explanation = data["sections"].get("Simplified Explanation", "")
        assert len(explanation) > 10

    @patch("app.generate", return_value=MOCK_NUMBERED_COLON)
    def test_all_valid_levels_accepted(self, mock_gen, client):
        for level in ("beginner", "intermediate", "expert"):
            response = client.post("/simplify", json={"topic": "gravity", "level": level})
            assert response.status_code == 200, f"Level '{level}' unexpectedly rejected"


# ── POST /simplify — Error Handling ──────────────────────────────────────────

class TestSimplifyErrors:

    @patch("app.generate", side_effect=EnvironmentError("WATSONX_API_KEY is not set"))
    def test_environment_error_returns_500(self, mock_gen, client):
        payload = {"topic": "topic", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 500
        data = response.get_json()
        assert data["success"] is False

    @patch("app.generate", side_effect=RuntimeError("IBM watsonx.ai API error: 401"))
    def test_runtime_error_returns_502(self, mock_gen, client):
        payload = {"topic": "topic", "level": "beginner"}
        response = client.post("/simplify", json=payload)
        assert response.status_code == 502
        data = response.get_json()
        assert data["success"] is False
        assert "error" in data


# ── parse_sections — unit tests covering all Granite output styles ────────────

class TestParseSections:

    def _parse(self, raw):
        from app import parse_sections
        return parse_sections(raw)

    def _all_labels(self):
        from prompts import SECTION_LABELS
        return SECTION_LABELS

    # ── Style A: numbered + colon ──────────────────────────────────────────

    def test_numbered_colon_all_sections_found(self):
        sections = self._parse(MOCK_NUMBERED_COLON)
        for label in self._all_labels():
            assert sections[label] != "Not available.", f"Section '{label}' not parsed"

    def test_numbered_colon_simplified_explanation_content(self):
        sections = self._parse(MOCK_NUMBERED_COLON)
        assert "photosynthesis" in sections["Simplified Explanation"].lower()

    def test_numbered_colon_key_concepts_has_bullets(self):
        sections = self._parse(MOCK_NUMBERED_COLON)
        assert "-" in sections["Key Concepts"] or "•" in sections["Key Concepts"]

    def test_numbered_colon_quiz_questions_present(self):
        sections = self._parse(MOCK_NUMBERED_COLON)
        assert len(sections["Quiz Questions"]) > 20

    # ── Style B: numbered, no colon ───────────────────────────────────────

    def test_numbered_no_colon_all_sections_found(self):
        sections = self._parse(MOCK_NUMBERED_NO_COLON)
        for label in self._all_labels():
            assert sections[label] != "Not available.", f"Section '{label}' not parsed (no-colon style)"

    def test_numbered_no_colon_content_correct(self):
        sections = self._parse(MOCK_NUMBERED_NO_COLON)
        assert len(sections["Simplified Explanation"]) > 5

    # ── Style C: Markdown bold **Heading:** ───────────────────────────────

    def test_markdown_bold_all_sections_found(self):
        sections = self._parse(MOCK_MARKDOWN_BOLD)
        for label in self._all_labels():
            assert sections[label] != "Not available.", f"Section '{label}' not parsed (bold style)"

    def test_markdown_bold_content_correct(self):
        sections = self._parse(MOCK_MARKDOWN_BOLD)
        assert "solar" in sections["Real-world Analogy"].lower()

    # ── Style D: Markdown ATX ## ──────────────────────────────────────────

    def test_markdown_atx_all_sections_found(self):
        sections = self._parse(MOCK_MARKDOWN_ATX)
        for label in self._all_labels():
            assert sections[label] != "Not available.", f"Section '{label}' not parsed (ATX style)"

    # ── Edge cases ────────────────────────────────────────────────────────

    def test_returns_all_section_keys_always(self):
        # Even on a good parse the dict must have all 7 keys
        sections = self._parse(MOCK_NUMBERED_COLON)
        for label in self._all_labels():
            assert label in sections

    def test_unparseable_text_goes_to_first_section(self):
        raw = "Some random text without any section headings at all."
        sections = self._parse(raw)
        assert sections[self._all_labels()[0]] == raw.strip()

    def test_duplicate_heading_only_first_kept(self):
        # If the model repeats a heading, only the first occurrence is used
        raw = (
            "1. Simplified Explanation:\nFirst content.\n\n"
            "1. Simplified Explanation:\nDuplicate content.\n\n"
            "2. Key Concepts:\nSome concepts.\n"
        )
        sections = self._parse(raw)
        assert "First content" in sections["Simplified Explanation"]
        assert "Duplicate" not in sections["Simplified Explanation"]

    def test_section_content_not_contaminated_by_next_heading(self):
        # Content of section 1 must not include the heading of section 2
        sections = self._parse(MOCK_NUMBERED_COLON)
        assert "Key Concepts" not in sections["Simplified Explanation"]

    def test_empty_string_falls_back_gracefully(self):
        sections = self._parse("")
        # Should return dict with all keys; first section gets empty fallback
        for label in self._all_labels():
            assert label in sections

    def test_case_insensitive_heading_match(self):
        # Granite may occasionally capitalise differently
        raw = (
            "1. SIMPLIFIED EXPLANATION:\nContent here.\n\n"
            "2. KEY CONCEPTS:\nBullets here.\n"
        )
        sections = self._parse(raw)
        assert sections["Simplified Explanation"] == "Content here."
        assert sections["Key Concepts"] == "Bullets here."

    # ── Style E: heading at position 0, no preceding newline (inline start) ──
    # This is the real-world failure mode: when the prompt ends with a
    # trailing newline Granite outputs "1. Simplified Explanation:\n<content>"
    # at the very start of generated_text with no blank line before it.

    def test_inline_start_heading_section1_not_empty(self):
        """Section 1 heading at position 0 must be found and its content extracted."""
        raw = (
            "1. Simplified Explanation:\n"
            "Photosynthesis converts light into chemical energy.\n\n"
            "2. Key Concepts:\n"
            "- Chlorophyll absorbs light\n\n"
            "3. Real-world Analogy:\n"
            "Like a solar panel.\n\n"
            "4. Example:\n"
            "A leaf on a sunny day.\n\n"
            "5. Important Terms:\n"
            "- Glucose: sugar made by plants\n\n"
            "6. Quick Revision:\n"
            "- Needs light, CO2, water\n\n"
            "7. Quiz Questions:\n"
            "Q1: What does photosynthesis produce?\n"
            "A) CO2  B) Glucose  C) Nitrogen  D) Water\n"
            "Answer: B\n"
        )
        sections = self._parse(raw)
        assert sections["Simplified Explanation"] != "Not available.", \
            "Section 1 was empty — inline-start heading not detected"
        assert "light" in sections["Simplified Explanation"].lower()

    def test_inline_start_all_sections_found(self):
        raw = (
            "1. Simplified Explanation:\n"
            "Photosynthesis converts light into chemical energy.\n\n"
            "2. Key Concepts:\n"
            "- Chlorophyll absorbs light\n\n"
            "3. Real-world Analogy:\n"
            "Like a solar panel.\n\n"
            "4. Example:\n"
            "A leaf on a sunny day.\n\n"
            "5. Important Terms:\n"
            "- Glucose: sugar made by plants\n\n"
            "6. Quick Revision:\n"
            "- Needs light, CO2, water\n\n"
            "7. Quiz Questions:\n"
            "Q1: What does photosynthesis produce?\n"
            "A) CO2  B) Glucose  C) Nitrogen  D) Water\n"
            "Answer: B\n"
        )
        sections = self._parse(raw)
        for label in self._all_labels():
            assert sections[label] != "Not available.", \
                f"Section '{label}' not parsed from inline-start output"

    def test_inline_start_section1_not_contaminated_by_later_sections(self):
        raw = (
            "1. Simplified Explanation:\n"
            "Short explanation here.\n\n"
            "2. Key Concepts:\n"
            "- Concept one\n"
        )
        sections = self._parse(raw)
        assert "Key Concepts" not in sections["Simplified Explanation"]
        assert sections["Simplified Explanation"] == "Short explanation here."
