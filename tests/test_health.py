from datetime import datetime, timedelta, timezone

from gh_summary.health import analyze_repo_health


def _repo(name, description=None, license_obj=None, days_old=30):
    updated = datetime.now(timezone.utc) - timedelta(days=days_old)
    return {
        "name": name,
        "description": description,
        "license": license_obj,
        "updated_at": updated.isoformat().replace("+00:00", "Z"),
    }


def test_analyze_repo_health_empty():
    result = analyze_repo_health([])
    assert result["score"] == 0
    assert result["total"] == 0
    assert result["issues"] == []
    assert result["repos_audit"] == []


def test_analyze_repo_health_perfect_score():
    repos = [
        _repo("a", "desc", {"key": "mit"}, days_old=10),
        _repo("b", "desc", {"key": "mit"}, days_old=20),
    ]
    result = analyze_repo_health(repos)
    assert result["score"] == 100
    assert result["total"] == 2
    assert result["has_description"] == 2
    assert result["has_license"] == 2
    assert result["recently_updated"] == 2
    assert result["issues"] == []


def test_analyze_repo_health_detects_issues():
    repos = [
        _repo("stale", None, None, days_old=400),
        _repo("ok", "desc", {"key": "mit"}, days_old=5),
    ]
    result = analyze_repo_health(repos)
    assert result["total"] == 2
    assert result["has_description"] == 1
    assert result["has_license"] == 1
    assert result["recently_updated"] == 1
    assert len(result["issues"]) == 3
    assert result["repos_audit"][0]["name"] == "stale"
    assert not result["repos_audit"][0]["has_description"]
    assert not result["repos_audit"][0]["has_license"]
    assert not result["repos_audit"][0]["is_active"]


def test_analyze_repo_health_score_calculation():
    repos = [
        _repo("only-desc", "desc", None, days_old=10),
        _repo("only-license", None, {"key": "mit"}, days_old=10),
    ]
    result = analyze_repo_health(repos)
    # 1/2 desc (17.5) + 1/2 license (17.5) + 2/2 active (30) = 65
    assert result["score"] == 65
