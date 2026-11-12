/**
 * script.js — EduSimplify frontend logic
 *
 * Handles:
 *   - Level selector toggle
 *   - Character count for textarea
 *   - Form submission via fetch (JSON)
 *   - Rendering the 7 result sections
 *   - Error display
 *   - "New Search" button
 */

// ── Section label → card element ID mapping ─────────────────────────────────
const SECTION_MAP = {
  "Simplified Explanation": "section-simplified-explanation",
  "Key Concepts":           "section-key-concepts",
  "Real-world Analogy":     "section-real-world-analogy",
  "Example":                "section-example",
  "Important Terms":        "section-important-terms",
  "Quick Revision":         "section-quick-revision",
  "Quiz Questions":         "section-quiz-questions",
};

// ── DOM references ────────────────────────────────────────────────────────────
const form         = document.getElementById("simplify-form");
const topicEl      = document.getElementById("topic");
const levelEl      = document.getElementById("level");
const charCountEl  = document.getElementById("char-count");
const formError    = document.getElementById("form-error");
const submitBtn    = document.getElementById("submit-btn");
const btnText      = submitBtn.querySelector(".btn-text");
const btnLoading   = submitBtn.querySelector(".btn-loading");
const resultsEl    = document.getElementById("results");
const apiError     = document.getElementById("api-error");
const apiErrorMsg  = document.getElementById("api-error-message");
const newSearchBtn = document.getElementById("new-search-btn");

// ── Level button toggle ───────────────────────────────────────────────────────
document.querySelectorAll(".level-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".level-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    levelEl.value = btn.dataset.level;
  });
});

// ── Character counter ─────────────────────────────────────────────────────────
topicEl.addEventListener("input", () => {
  charCountEl.textContent = `${topicEl.value.length} / 2000`;
});

// ── Form submission ───────────────────────────────────────────────────────────
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors();

  const topic = topicEl.value.trim();
  const level = levelEl.value;

  // Client-side validation
  if (!topic) {
    showFormError("Please enter a topic before clicking Simplify.");
    topicEl.focus();
    return;
  }

  setLoading(true);
  hideResults();

  try {
    const response = await fetch("/simplify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, level }),
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      showApiError(data.error || `Server error (${response.status}). Please try again.`);
      return;
    }

    renderSections(data.sections);
    showResults();

  } catch (err) {
    // Network error (no internet, server down, etc.)
    showApiError(
      "Could not reach the server. Please check your internet connection and try again."
    );
  } finally {
    setLoading(false);
  }
});

// ── "New Search" resets UI ────────────────────────────────────────────────────
newSearchBtn.addEventListener("click", () => {
  hideResults();
  clearErrors();
  form.reset();
  charCountEl.textContent = "0 / 2000";
  // Reset level buttons to Beginner
  document.querySelectorAll(".level-btn").forEach(b => b.classList.remove("active"));
  document.querySelector('.level-btn[data-level="beginner"]').classList.add("active");
  levelEl.value = "beginner";
  topicEl.focus();
  // Scroll back to input
  form.scrollIntoView({ behavior: "smooth", block: "start" });
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function setLoading(on) {
  submitBtn.disabled = on;
  btnText.hidden     = on;
  btnLoading.hidden  = !on;
}

function showFormError(msg) {
  formError.textContent = msg;
  formError.hidden = false;
}

function showApiError(msg) {
  apiErrorMsg.textContent = msg;
  apiError.hidden = false;
  apiError.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function clearErrors() {
  formError.hidden = true;
  formError.textContent = "";
  apiError.hidden = true;
  apiErrorMsg.textContent = "";
}

function hideResults() {
  resultsEl.hidden = true;
}

function showResults() {
  resultsEl.hidden = false;
  resultsEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

/**
 * Populate each result card with the model's output.
 *
 * @param {Object} sections - Keys are section labels, values are text content.
 */
function renderSections(sections) {
  for (const [label, cardId] of Object.entries(SECTION_MAP)) {
    const card = document.getElementById(cardId);
    if (!card) continue;

    const contentEl = card.querySelector(".section-content");
    const text = (sections[label] || "").trim();

    if (text && text !== "Not available.") {
      contentEl.textContent = text;
    } else {
      contentEl.textContent = "The model did not provide this section. Try rephrasing your topic.";
      contentEl.style.color = "#888";
    }
  }
}
