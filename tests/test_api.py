from datetime import datetime, timezone

import httpx

from gh_summary.api import github_error_message, github_headers, raise_for_github


def test_github_headers_user_agent_and_optional_token(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    headers = github_headers()
    assert headers["User-Agent"].startswith("gh-summary-cli")
    assert "Authorization" not in headers

    monkeypatch.setenv("GH_TOKEN", "secret-token")
    assert github_headers()["Authorization"] == "Bearer secret-token"


def test_rate_limit_message_includes_reset_and_token_hint():
    reset = int(datetime(2026, 8, 19, 1, 30, tzinfo=timezone.utc).timestamp())
    response = httpx.Response(
        403,
        headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": str(reset)},
        text="API rate limit exceeded",
    )
    msg = github_error_message(response, "octocat")
    assert "Límite de la API de GitHub alcanzado" in msg
    assert "GITHUB_TOKEN" in msg
    assert "Reintenta a las" in msg


def test_raise_for_github_404():
    response = httpx.Response(404, text="Not Found")
    try:
        raise_for_github(response, "nobody")
        assert False, "expected ValueError"
    except ValueError as err:
        assert "nobody" in str(err)


def test_github_error_message_401():
    response = httpx.Response(401, text="Bad credentials")
    msg = github_error_message(response, "octocat")
    assert "Token de GitHub inválido" in msg
    assert "GITHUB_TOKEN" in msg


def test_raise_for_github_success():
    response = httpx.Response(200, json={"login": "octocat"})
    raise_for_github(response, "octocat")


def test_github_headers_prefers_github_token(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "gh-token")
    monkeypatch.setenv("GH_TOKEN", "alt-token")
    assert github_headers()["Authorization"] == "Bearer gh-token"
