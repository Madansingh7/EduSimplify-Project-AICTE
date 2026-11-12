"""
tests/test_watsonx.py — Unit tests for watsonx_client.py

All HTTP calls are mocked — no real IBM API calls are made.
"""

import pytest
from unittest.mock import patch, MagicMock
import os

import watsonx_client


# ── Helper: fake IAM token response ──────────────────────────────────────────

def fake_iam_response():
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"access_token": "fake-token-abc123"}
    mock.raise_for_status.return_value = None
    return mock


def fake_watsonx_response(text="Great explanation here."):
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {
        "results": [{"generated_text": text}]
    }
    mock.raise_for_status.return_value = None
    return mock


# ── Tests for _get_required_env ───────────────────────────────────────────────

class TestGetRequiredEnv:

    def test_raises_when_env_var_missing(self, monkeypatch):
        monkeypatch.delenv("WATSONX_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="WATSONX_API_KEY"):
            watsonx_client._get_required_env("WATSONX_API_KEY")

    def test_returns_value_when_set(self, monkeypatch):
        monkeypatch.setenv("WATSONX_API_KEY", "mykey")
        result = watsonx_client._get_required_env("WATSONX_API_KEY")
        assert result == "mykey"

    def test_raises_when_env_var_empty(self, monkeypatch):
        monkeypatch.setenv("WATSONX_API_KEY", "   ")
        with pytest.raises(EnvironmentError, match="WATSONX_API_KEY"):
            watsonx_client._get_required_env("WATSONX_API_KEY")


# ── Tests for get_iam_token ───────────────────────────────────────────────────

class TestGetIamToken:

    @patch("watsonx_client.requests.post")
    def test_returns_token_on_success(self, mock_post):
        mock_post.return_value = fake_iam_response()
        token = watsonx_client.get_iam_token("my-api-key")
        assert token == "fake-token-abc123"

    @patch("watsonx_client.requests.post")
    def test_raises_runtime_error_when_no_access_token(self, mock_post):
        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {}  # no access_token key
        mock.raise_for_status.return_value = None
        mock_post.return_value = mock
        with pytest.raises(RuntimeError, match="access_token"):
            watsonx_client.get_iam_token("bad-key")

    @patch("watsonx_client.requests.post")
    def test_raises_runtime_error_on_timeout(self, mock_post):
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout()
        with pytest.raises(RuntimeError, match="Timed out"):
            watsonx_client.get_iam_token("any-key")

    @patch("watsonx_client.requests.post")
    def test_raises_runtime_error_on_http_error(self, mock_post):
        from requests.exceptions import HTTPError
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("401 Unauthorized")
        mock_resp.json.return_value = {}
        mock_post.return_value = mock_resp
        with pytest.raises(RuntimeError, match="authentication failed"):
            watsonx_client.get_iam_token("bad-key")


# ── Tests for generate ────────────────────────────────────────────────────────

class TestGenerate:

    ENV = {
        "WATSONX_API_KEY":    "test-api-key",
        "WATSONX_PROJECT_ID": "test-project-id",
        "WATSONX_URL":        "https://us-south.ml.cloud.ibm.com",
        "WATSONX_MODEL_ID":   "ibm/granite-4-h-small",
    }

    @patch("watsonx_client.requests.post")
    def test_returns_generated_text(self, mock_post, monkeypatch):
        for k, v in self.ENV.items():
            monkeypatch.setenv(k, v)

        # First call = IAM token, second call = watsonx inference
        mock_post.side_effect = [
            fake_iam_response(),
            fake_watsonx_response("This is the answer."),
        ]

        result = watsonx_client.generate("Explain gravity.")
        assert result == "This is the answer."

    @patch("watsonx_client.requests.post")
    def test_raises_on_empty_generated_text(self, mock_post, monkeypatch):
        for k, v in self.ENV.items():
            monkeypatch.setenv(k, v)

        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"results": [{"generated_text": "   "}]}
        mock.raise_for_status.return_value = None

        mock_post.side_effect = [fake_iam_response(), mock]

        with pytest.raises(RuntimeError, match="empty response"):
            watsonx_client.generate("Explain anything.")

    @patch("watsonx_client.requests.post")
    def test_raises_on_malformed_response(self, mock_post, monkeypatch):
        for k, v in self.ENV.items():
            monkeypatch.setenv(k, v)

        mock = MagicMock()
        mock.status_code = 200
        mock.json.return_value = {"unexpected_key": "value"}  # no "results"
        mock.raise_for_status.return_value = None

        mock_post.side_effect = [fake_iam_response(), mock]

        with pytest.raises(RuntimeError, match="Unexpected response format"):
            watsonx_client.generate("Explain anything.")

    def test_raises_environment_error_when_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("WATSONX_API_KEY", raising=False)
        monkeypatch.setenv("WATSONX_PROJECT_ID", "pid")
        monkeypatch.setenv("WATSONX_URL", "https://example.com")
        monkeypatch.setenv("WATSONX_MODEL_ID", "ibm/granite-4-h-small")

        with pytest.raises(EnvironmentError, match="WATSONX_API_KEY"):
            watsonx_client.generate("Test prompt")

    @patch("watsonx_client.requests.post")
    def test_trailing_slash_in_url_is_handled(self, mock_post, monkeypatch):
        env = dict(self.ENV)
        env["WATSONX_URL"] = "https://us-south.ml.cloud.ibm.com/"
        for k, v in env.items():
            monkeypatch.setenv(k, v)

        mock_post.side_effect = [
            fake_iam_response(),
            fake_watsonx_response("OK"),
        ]

        result = watsonx_client.generate("Test")
        # Verify the endpoint URL has no double slash
        call_url = mock_post.call_args_list[1][0][0]
        assert "//" not in call_url.replace("https://", "")
