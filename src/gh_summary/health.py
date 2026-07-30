from datetime import datetime, timezone

def analyze_repo_health(repos_data: list) -> dict:
    if not repos_data:
        return {"score": 0, "total": 0, "issues": [], "repos_audit": []}

    total = len(repos_data)
    has_description = 0
    has_license = 0
    recently_updated = 0
    now = datetime.now(timezone.utc)
    repos_audit = []

    for repo in repos_data:
        desc = bool(repo.get("description"))
        license_attr = bool(repo.get("license"))
        
        updated_at_str = repo.get("updated_at")
        is_active = False
        if updated_at_str:
            updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            is_active = (now - updated_at).days <= 365

        if desc: has_description += 1
        if license_attr: has_license += 1
        if is_active: recently_updated += 1

        repos_audit.append({
            "name": repo.get("name"),
            "has_description": desc,
            "has_license": license_attr,
            "is_active": is_active,
        })

    total_score = round(((has_description / total) * 35) + ((has_license / total) * 35) + ((recently_updated / total) * 30))

    issues = []
    if total - has_description > 0:
        issues.append(f"⚠️ {total - has_description} repositorio(s) no tienen descripción.")
    if total - has_license > 0:
        issues.append(f"📜 {total - has_license} repositorio(s) no tienen una LICENCIA definida.")
    if total - recently_updated > 0:
        issues.append(f"💤 {total - recently_updated} repositorio(s) sin actualizaciones este año.")

    return {
        "score": total_score,
        "total": total,
        "has_description": has_description,
        "has_license": has_license,
        "recently_updated": recently_updated,
        "issues": issues,
        "repos_audit": repos_audit,
    }