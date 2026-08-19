from datetime import datetime, timezone

from gh_summary.formatters import (
    calculate_language_stats,
    format_as_markdown,
    format_compact_number,
    format_progress_bar,
    format_ratio_bar,
    format_relative_date,
)


def test_calculate_language_stats_success():
    mock_repos = [
        {'name': 'repo1', 'language': 'Python'},
        {'name': 'repo2', 'language': 'Python'},
        {'name': 'repo3', 'language': 'Java'},
    ]
    stats = calculate_language_stats(mock_repos)
    assert len(stats) == 2
    assert stats[0]['language'] == 'Python'
    assert stats[0]['count'] == 2

def test_calculate_language_stats_empty():
    mock_repos = [{'name': 'repo1', 'language': None}]
    stats = calculate_language_stats(mock_repos)
    assert stats == []


def test_format_compact_number():
    assert format_compact_number(999) == "999"
    assert format_compact_number(1500) == "1.5k"
    assert format_compact_number(2_500_000) == "2.5M"


def test_format_progress_bar():
    assert len(format_progress_bar(50, width=10)) == 10
    assert format_progress_bar(0, width=5) == "░░░░░"
    assert format_progress_bar(100, width=5) == "█████"


def test_format_ratio_bar():
    assert "4/5 (80%)" in format_ratio_bar(4, 5)
    assert "0/0 (0%)" in format_ratio_bar(0, 0)


def test_format_relative_date():
    assert format_relative_date(None) == "N/A"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assert format_relative_date(today) == "hoy"


def test_format_as_markdown_includes_profile_and_repos():
    user = {
        "login": "dev",
        "name": "Developer",
        "bio": "Hello",
        "html_url": "https://github.com/dev",
        "followers": 1200,
        "following": 10,
        "public_repos": 3,
        "location": "Earth",
    }
    repos = [
        {
            "name": "demo",
            "language": "Python",
            "stargazers_count": 1500,
            "forks_count": 20,
            "html_url": "https://github.com/dev/demo",
            "updated_at": "2026-08-18T00:00:00Z",
        }
    ]
    md = format_as_markdown(user, calculate_language_stats(repos), repos)
    assert "Developer (@dev)" in md
    assert "[demo](https://github.com/dev/demo)" in md
    assert "1.5k" in md
