"""
app.py — EduSimplify Flask application.

Routes:
    GET  /          — Serve the main UI page.
    POST /simplify  — Accept topic + level, call watsonx.ai, return JSON.
"""

import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from prompts import build_prompt, SECTION_LABELS
from watsonx_client import generate

# Load environment variables from .env (ignored if .env doesn't exist)
load_dotenv()

app = Flask(__name__)


def parse_sections(raw_text: str) -> dict:
    """
    Parse Granite's raw output into the 7 named sections.

    Granite may produce any of these heading styles:
        1. Simplified Explanation:          ← numbered with colon
        1. Simplified Explanation           ← numbered without colon
        ## Simplified Explanation:          ← Markdown ATX heading
        **Simplified Explanation:**         ← Markdown bold
        Simplified Explanation:             ← plain with colon

    Strategy:
        1. Build one regex that matches ALL heading variants for ALL labels.
        2. Collect every match position and its canonical label.
        3. Build an ordered list of all heading positions (including duplicates)
           so that the content slice for each unique label is bounded correctly.
        4. Deduplicate — keep only the first occurrence of each label.

    Args:
        raw_text: The full generated text from the model.

    Returns:
        A dict with SECTION_LABELS as keys and section text as values.
        Labels not found get value "Not available.".
    """
    import re

    result = {label: "Not available." for label in SECTION_LABELS}

    escaped_labels = [re.escape(label) for label in SECTION_LABELS]
    label_pattern = "|".join(escaped_labels)

    # Primary pattern: heading occupies its own line (MULTILINE ^ … $).
    # Handles:
    #   1. Simplified Explanation:    ← numbered + colon
    #   1. Simplified Explanation     ← numbered, no colon
    #   ## Simplified Explanation     ← ATX Markdown
    #   **Simplified Explanation:**   ← bold Markdown
    #   Simplified Explanation:       ← plain + colon
    line_heading_re = re.compile(
        r"^\*{0,2}(?:#{1,3}\s*)?(?:\d+\.\s*)?"   # optional prefix
        r"(" + label_pattern + r")"               # captured label (group 1)
        r"\*{0,2}\s*:?\*{0,2}\s*$",              # optional trailing ** / colon
        re.IGNORECASE | re.MULTILINE,
    )

    # Secondary pattern: heading at the very start of the generated text.
    # When the prompt ends without a trailing newline, Granite may continue
    # inline so the first heading is at position 0 with no preceding newline.
    # This pattern matches only at the start of the string (re.DOTALL not needed).
    start_heading_re = re.compile(
        r"^\*{0,2}(?:#{1,3}\s*)?(?:\d+\.\s*)?"
        r"(" + label_pattern + r")"
        r"\*{0,2}\s*:?\*{0,2}\s*\n",             # must be followed by a newline
        re.IGNORECASE,
    )

    # Collect ALL matches (including duplicates) as (match_start, match_end, canonical)
    all_matches = []

    def _resolve(m: re.Match) -> str | None:
        """Return the canonical SECTION_LABELS entry for a regex match, or None."""
        matched_text = m.group(1).strip()
        return next(
            (lbl for lbl in SECTION_LABELS if lbl.lower() == matched_text.lower()),
            None,
        )

    # Check for an inline heading at the very start of the text first.
    # start_heading_re includes the trailing \n in its match, so m.start() == 0
    # but m.end() > line_heading_re's m.end() for the same position.
    # We record m.start() as the heading start and m.end() as where content begins.
    m0 = start_heading_re.match(raw_text)
    if m0:
        canonical = _resolve(m0)
        if canonical:
            all_matches.append((m0.start(), m0.end(), canonical))

    # Collect all line-anchored headings, skipping position 0 if already captured.
    start0_captured = bool(all_matches)
    for m in line_heading_re.finditer(raw_text):
        if start0_captured and m.start() == 0:
            continue   # already added via start_heading_re
        canonical = _resolve(m)
        if canonical:
            # Skip exact-position duplicates
            if not all_matches or all_matches[-1][0] != m.start():
                all_matches.append((m.start(), m.end(), canonical))

    if not all_matches:
        # Fallback: model didn't follow the format — put everything under section 1.
        result[SECTION_LABELS[0]] = raw_text.strip()
        return result

    # Build unique_matches (first occurrence of each label).
    # Use all_matches (including duplicates) to correctly bound content —
    # content ends at the NEXT heading start, even if that heading is a duplicate.
    seen: set = set()
    unique_matches = []   # list of (content_start, content_end, label)

    for idx, (start, end, label) in enumerate(all_matches):
        if label not in seen:
            seen.add(label)
            next_heading_start = (
                all_matches[idx + 1][0] if idx + 1 < len(all_matches) else len(raw_text)
            )
            unique_matches.append((end, next_heading_start, label))

    # Maximum characters per section — prevents a runaway section from
    # consuming content that belongs to later sections when Granite omits
    # a heading.  1 200 chars is generous for any concise section.
    MAX_SECTION_CHARS = 1200

    # Extract content for each unique section.
    for content_start, content_end, label in unique_matches:
        content = raw_text[content_start:content_end].strip()
        if content:
            result[label] = content[:MAX_SECTION_CHARS]

    return result


@app.route("/")
def index():
    """Serve the main UI page."""
    return render_template("index.html")


@app.route("/simplify", methods=["POST"])
def simplify():
    """
    Accept a topic and level, call watsonx.ai, and return the 7 sections as JSON.

    Request JSON body:
        { "topic": "...", "level": "beginner|intermediate|expert" }

    Success response (200):
        {
            "success": true,
            "sections": {
                "Simplified Explanation": "...",
                "Key Concepts": "...",
                ...
            }
        }

    Error response (400 / 500 / 502):
        { "success": false, "error": "Human-readable message" }
    """
    data = request.get_json(silent=True)

    # --- Input validation ---
    if not data:
        return jsonify({"success": False, "error": "Request body must be JSON."}), 400

    topic = (data.get("topic") or "").strip()
    level = (data.get("level") or "").strip().lower()

    if not topic:
        return jsonify({"success": False, "error": "Please enter a topic."}), 400

    if len(topic) > 2000:
        return jsonify(
            {"success": False, "error": "Topic is too long. Please keep it under 2000 characters."}
        ), 400

    valid_levels = ("beginner", "intermediate", "expert")
    if level not in valid_levels:
        return jsonify(
            {"success": False, "error": f"Level must be one of: {', '.join(valid_levels)}."}
        ), 400

    # --- Build prompt ---
    try:
        prompt = build_prompt(topic, level)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    # --- Call IBM watsonx.ai ---
    try:
        raw_text = generate(prompt)
    except EnvironmentError as exc:
        # Missing credentials — server configuration issue
        app.logger.error("Environment configuration error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
    except RuntimeError as exc:
        # API / network / auth errors
        app.logger.error("watsonx.ai error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 502

    # --- Parse sections ---
    sections = parse_sections(raw_text)

    return jsonify({"success": True, "sections": sections}), 200


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
