# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

**EduSimplify** — AICTE × IBM student project. Python Flask app using IBM watsonx.ai (Granite) to simplify academic content into 7 structured sections.

## Commands

```bash
# Run the app
python app.py                         # http://localhost:5000

# Run all tests (no IBM credentials needed — all HTTP is mocked)
pytest tests/ -v

# Run a single test file
pytest tests/test_app.py -v

# Run a single test by name
pytest tests/test_app.py::TestSimplifyValidation::test_empty_topic_returns_400 -v

# Install dependencies
pip install -r requirements.txt
```

## Non-obvious Architecture

- **IAM token exchange happens on every request** in `watsonx_client.py` — there is no token cache. This is intentional simplicity.
- `parse_sections()` in `app.py` parses the model's raw text by searching for numbered headings (`1. Simplified Explanation:`). If the model skips numbering, it falls back to the plain heading form. If both fail, the full text goes into the first section.
- The prompt in `prompts.py` instructs Granite to produce exactly 7 sections. Changing the section names in `SECTION_LABELS` requires updating the prompt text, the HTML card IDs in `templates/index.html`, and the `SECTION_MAP` in `static/script.js` — all three must stay in sync.

## Critical Patterns

- **Credentials**: Read exclusively from `os.environ` via `_get_required_env()` in `watsonx_client.py`. Never read directly with `os.environ["KEY"]` — use the helper so missing vars give a clear error.
- **Endpoint**: `{WATSONX_URL}/ml/v1/text/generation?version=2023-05-29` — the base URL has its trailing slash stripped before building this URL.
- **Test isolation**: Tests mock `watsonx_client.generate` at the `app` module level (`@patch("app.generate", ...)`), not at the `watsonx_client` module level.
- **No `tests/__init__.py`**: pytest finds tests without it; adding one is unnecessary.

## Environment Variables Required

| Variable | Example value |
|---|---|
| `WATSONX_API_KEY` | *(your IBM Cloud API key — set in `.env` locally)* |
| `WATSONX_PROJECT_ID` | *(your watsonx.ai project ID — set in `.env` locally)* |
| `WATSONX_URL` | `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | `ibm/granite-4-h-small` |

Copy `.env.example` → `.env` and fill in `WATSONX_API_KEY`. The `.env` file is gitignored.
