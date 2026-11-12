"""
watsonx_client.py — IBM watsonx.ai API wrapper.

Flow:
  1. Read credentials from environment variables.
  2. Exchange the IBM Cloud API key for a short-lived IAM Bearer token.
  3. POST the prompt to the watsonx.ai text generation endpoint.
  4. Return the generated text.

All credentials are read from environment variables — nothing is hardcoded.
"""

import os
import requests
from requests.exceptions import RequestException, Timeout

# IBM IAM token endpoint (always this URL, regardless of region)
IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

# Timeout in seconds for HTTP requests
REQUEST_TIMEOUT = 60


def _get_required_env(name: str) -> str:
    """Read a required environment variable or raise a clear error."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
    return value


def get_iam_token(api_key: str) -> str:
    """
    Exchange an IBM Cloud API key for a short-lived IAM Bearer token.

    Args:
        api_key: The IBM Cloud API key (read from env, never logged).

    Returns:
        A Bearer token string.

    Raises:
        RuntimeError: If authentication fails.
    """
    try:
        response = requests.post(
            IAM_TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": api_key,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Timeout:
        raise RuntimeError(
            "Timed out while connecting to IBM IAM. Check your internet connection."
        )
    except RequestException as exc:
        raise RuntimeError(f"IBM IAM authentication failed: {exc}") from exc

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(
            "IBM IAM returned a response but it contained no access_token. "
            "Check that your API key is valid."
        )
    return token


def generate(prompt: str) -> str:
    """
    Send a prompt to IBM watsonx.ai and return the generated text.

    Reads the following environment variables:
        WATSONX_API_KEY    — IBM Cloud API key
        WATSONX_PROJECT_ID — watsonx.ai project ID
        WATSONX_URL        — base URL, e.g. https://us-south.ml.cloud.ibm.com
        WATSONX_MODEL_ID   — model ID, e.g. ibm/granite-4-h-small

    Args:
        prompt: The fully built prompt string.

    Returns:
        The model's generated text as a plain string.

    Raises:
        EnvironmentError: If required env vars are missing.
        RuntimeError: If the API call fails or returns an unexpected response.
    """
    api_key = _get_required_env("WATSONX_API_KEY")
    project_id = _get_required_env("WATSONX_PROJECT_ID")
    base_url = _get_required_env("WATSONX_URL").rstrip("/")
    model_id = _get_required_env("WATSONX_MODEL_ID")

    # Step 1: Get IAM token
    token = get_iam_token(api_key)

    # Step 2: Call watsonx.ai text generation endpoint
    endpoint = f"{base_url}/ml/v1/text/generation?version=2023-05-29"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "model_id": model_id,
        "project_id": project_id,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 2000,  # 7 full sections + 3 MCQs needs headroom
            "repetition_penalty": 1.1,
        },
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Timeout:
        raise RuntimeError(
            "The request to IBM watsonx.ai timed out. "
            "The model may be busy — please try again."
        )
    except RequestException as exc:
        # Extract a human-readable message if the API returned JSON error details
        try:
            err_detail = exc.response.json()
            err_msg = err_detail.get("errors", [{}])[0].get("message") or str(exc)
        except Exception:
            err_msg = str(exc)
        raise RuntimeError(f"IBM watsonx.ai API error: {err_msg}") from exc

    # Step 3: Parse the response
    data = response.json()
    try:
        generated_text = data["results"][0]["generated_text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            f"Unexpected response format from IBM watsonx.ai: {data}"
        ) from exc

    if not generated_text or not generated_text.strip():
        raise RuntimeError(
            "IBM watsonx.ai returned an empty response. "
            "Try rephrasing your topic or selecting a different level."
        )

    return generated_text.strip()
