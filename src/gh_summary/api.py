import asyncio
import os
from datetime import datetime, timezone

import httpx

USER_AGENT = "gh-summary-cli (https://github.com/ValentinAguayo1/gh-summary-cli)"


def github_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_error_message(response: httpx.Response, username: str) -> str:
    if response.status_code == 404:
        return f"El usuario '{username}' no existe en GitHub."
    if response.status_code == 401:
        return "Token de GitHub inválido. Revisa GITHUB_TOKEN o GH_TOKEN."
    if response.status_code in (403, 429):
        remaining = response.headers.get("x-ratelimit-remaining")
        reset = response.headers.get("x-ratelimit-reset")
        retry_after = response.headers.get("retry-after")
        body = (response.text or "").lower()
        is_rate_limit = (
            response.status_code == 429
            or remaining == "0"
            or "rate limit" in body
        )
        if is_rate_limit:
            hint = " Configura GITHUB_TOKEN o GH_TOKEN para subir el límite (5000 req/h)."
            if retry_after:
                return f"Límite de la API de GitHub alcanzado. Reintenta en {retry_after}s.{hint}"
            if reset:
                reset_local = datetime.fromtimestamp(int(reset), tz=timezone.utc).astimezone()
                return (
                    f"Límite de la API de GitHub alcanzado. "
                    f"Reintenta a las {reset_local.strftime('%H:%M:%S')}.{hint}"
                )
            return f"Límite de la API de GitHub alcanzado.{hint}"
        return (
            f"GitHub rechazó la petición (HTTP {response.status_code}). "
            "Prueba con GITHUB_TOKEN o GH_TOKEN."
        )
    return f"Error de GitHub (HTTP {response.status_code})."


def raise_for_github(response: httpx.Response, username: str) -> None:
    if response.is_success:
        return
    if response.status_code in (401, 403, 404, 429):
        raise ValueError(github_error_message(response, username))
    response.raise_for_status()


async def fetch_github_data(username: str):
    url_user = f"https://api.github.com/users/{username}"
    url_repos = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"

    async with httpx.AsyncClient(timeout=10.0, headers=github_headers()) as client:
        res_user, res_repos = await asyncio.gather(
            client.get(url_user),
            client.get(url_repos),
        )

    raise_for_github(res_user, username)
    raise_for_github(res_repos, username)

    return res_user.json(), res_repos.json()
