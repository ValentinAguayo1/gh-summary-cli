import json

from typer.testing import CliRunner

from gh_summary.cli import app

runner = CliRunner()

_USER = {
    "login": "dev",
    "name": "Developer",
    "bio": "Hello",
    "html_url": "https://github.com/dev",
    "followers": 1,
    "following": 1,
    "public_repos": 0,
    "location": "Earth",
}


def _patch_fetch(monkeypatch, side_effect):
    monkeypatch.setattr("gh_summary.cli.fetch_github_data", side_effect)


def test_no_args_shows_help():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "fetch" in result.stdout
    assert "health" in result.stdout


def test_invalid_format_exits_nonzero():
    result = runner.invoke(app, ["fetch", "dev", "--format", "xml"])
    assert result.exit_code != 0
    combined = ((result.stdout or "") + (result.stderr or "")).lower()
    assert "xml" in combined or "invalid" in combined or "md" in combined


def test_fetch_user_error_exits_1(monkeypatch):
    async def boom(username):
        raise ValueError(f"El usuario '{username}' no existe en GitHub.")

    _patch_fetch(monkeypatch, boom)
    result = runner.invoke(app, ["fetch", "nobody"])
    assert result.exit_code == 1
    assert "nobody" in result.stdout


def test_health_user_error_exits_1(monkeypatch):
    async def boom(username):
        raise ValueError(f"El usuario '{username}' no existe en GitHub.")

    _patch_fetch(monkeypatch, boom)
    result = runner.invoke(app, ["health", "nobody"])
    assert result.exit_code == 1
    assert "nobody" in result.stdout
    assert "conexión" not in result.stdout


def test_fetch_json_ok(monkeypatch):
    async def ok(_username):
        return _USER, []

    _patch_fetch(monkeypatch, ok)
    result = runner.invoke(app, ["fetch", "dev", "-f", "json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["user"]["login"] == "dev"
    assert data["recent_repos"] == []
