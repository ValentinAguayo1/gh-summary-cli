import asyncio
import httpx

async def fetch_github_data(username: str):
    url_user = f"https://api.github.com/users/{username}"
    url_repos = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"

    async with httpx.AsyncClient(timeout=10.0) as client:
        user_task = client.get(url_user)
        repos_task = client.get(url_repos)
        res_user, res_repos = await asyncio.gather(user_task, repos_task)

    if res_user.status_code == 404:
        raise ValueError(f"El usuario '{username}' no existe en GitHub.")

    res_user.raise_for_status()
    res_repos.raise_for_status()

    return res_user.json(), res_repos.json()