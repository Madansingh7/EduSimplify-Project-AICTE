"""
prompts.py — Builds structured prompts for the Granite model.
"""

LEVEL_DESCRIPTIONS = {
    "beginner": (
        "a complete beginner with no prior knowledge. "
        "Use very simple words, short sentences, and friendly analogies."
    ),
    "intermediate": (
        "someone with basic familiarity with the subject. "
        "Use clear explanations and introduce technical terms with brief definitions."
    ),
    "expert": (
        "an advanced learner or professional. "
        "Use precise technical language, depth, and nuance, but remain concise."
    ),
}

SECTION_LABELS = [
    "Simplified Explanation",
    "Key Concepts",
    "Real-world Analogy",
    "Example",
    "Important Terms",
    "Quick Revision",
    "Quiz Questions",
]


def build_prompt(topic: str, level: str) -> str:
    """Build the structured prompt sent to IBM Granite."""

    level_key = level.strip().lower()

    if level_key not in LEVEL_DESCRIPTIONS:
        raise ValueError(
            f"Invalid level '{level}'. Must be one of: "
            f"{', '.join(LEVEL_DESCRIPTIONS)}"
        )

    audience = LEVEL_DESCRIPTIONS[level_key]

    prompt = (
        f"You are an expert educator. Explain the following topic for {audience}\n\n"
        f"TOPIC: {topic}\n\n"

        "IMPORTANT OUTPUT RULES:\n"
        "Generate exactly 7 sections using the exact headings below. "
        "Each heading must appear exactly as written, on its own line, followed by a colon. "
        "Do not use labels such as S1, S2, S3, S4, S5, S6, S7, [S1], [S2], "
        "or any other section labels. "
        "Do not omit any section. "
        "Do not add extra sections. "
        "Do not add an introduction before the first heading or commentary after the final section.\n\n"

        "REQUIRED HEADINGS IN THIS EXACT ORDER:\n"
        "1. Simplified Explanation:\n"
        "2. Key Concepts:\n"
        "3. Real-world Analogy:\n"
        "4. Example:\n"
        "5. Important Terms:\n"
        "6. Quick Revision:\n"
        "7. Quiz Questions:\n\n"

        "CONTENT REQUIREMENTS:\n"
        "Simplified Explanation: 2-4 concise sentences. Stay strictly on-topic.\n"
        "Key Concepts: exactly 3-5 short bullet points, each starting with a dash.\n"
        "Real-world Analogy: exactly 1 relatable sentence.\n"
        "Example: 1-3 concrete, topic-specific sentences.\n"
        "Important Terms: exactly 4-6 relevant terms. "
        "Format each as 'Term: definition.' "
        "Do not include unrelated terms or extra prose.\n"
        "Quick Revision: exactly 3-5 short bullet points, each starting with a dash.\n"
        "Quiz Questions: exactly 3 multiple-choice questions. "
        "Each question must have four options A), B), C), D) "
        "and one Answer line.\n\n"

        "For Expert level, use technically accurate and precise language, "
        "but remain concise. "
        "Never produce filler, unrelated content, invented sections, "
        "or placeholder text.\n\n"

        "Begin your response immediately with the first required section and "
        "place its content on the following line.\n"
    )

    return prompt