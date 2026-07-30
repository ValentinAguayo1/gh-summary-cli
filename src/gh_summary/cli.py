from collections import Counter
import asyncio
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
import typer

app = typer.Typer(
    help="Herramienta CLI para obtener resúmenes visuales de perfiles de GitHub."
)
console = Console()


def calculate_language_stats(repos_data: list) -> list:
    """Calcula la frecuencia y porcentaje de uso de los lenguajes principales."""
    languages = [repo.get("language") for repo in repos_data if repo.get("language")]
    if not languages:
        return []

    total_langs = len(languages)
    lang_counts = Counter(languages)

    stats = []
    for lang, count in lang_counts.most_common(5):
        pct = (count / total_langs) * 100
        stats.append({"language": lang, "count": count, "percentage": pct})
    return stats


async def fetch_github_data(username: str):
    """Realiza peticiones asíncronas simultáneas a la API de GitHub."""
    url_user = f"https://api.github.com/users/{username}"
    url_repos = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Peticiones en paralelo con asyncio
        user_task = client.get(url_user)
        repos_task = client.get(url_repos)
        res_user, res_repos = await asyncio.gather(user_task, repos_task)

    if res_user.status_code == 404:
        raise ValueError(f"El usuario '{username}' no existe en GitHub.")

    res_user.raise_for_status()
    res_repos.raise_for_status()

    return res_user.json(), res_repos.json()


@app.command(name="fetch")
def fetch(
    username: str,
    limit: int = typer.Option(5, help="Número de repositorios a mostrar en la tabla."),
):
    """Obtiene y despliega un Dashboard interactivo del perfil de GitHub."""

    with console.status(
        f"[bold blue]Consultando API de GitHub para @{username}...[/bold blue]",
        spinner="dots",
    ):
        try:
            user_data, repos_data = asyncio.run(fetch_github_data(username))
        except ValueError as err:
            console.print(f"[bold red]❌ Error:[/bold red] {err}")
            return
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión:[/bold red] {e}")
            return

    console.clear()  # Limpia la pantalla para un efecto de app nativa

    # --- 1. PANEL DE PERFIL (IZQUIERDA) ---
    bio = user_data.get("bio") or "Sin biografía disponible."
    profile_text = (
        f"[bold white]{user_data.get('name', username)}[/bold white] (@{username})\n"
        f"[dim]{bio}[/dim]\n\n"
        f"📍 [cyan]Ubicación:[/cyan] {user_data.get('location', 'N/A')}\n"
        f"👥 [cyan]Seguidores:[/cyan] {user_data.get('followers')}  |  [cyan]Siguiendo:[/cyan] {user_data.get('following')}\n"
        f"📦 [cyan]Repositorios Públicos:[/cyan] {user_data.get('public_repos')}"
    )
    profile_panel = Panel(
        profile_text,
        title="👤 Perfil de GitHub",
        border_style="magenta",
        padding=(1, 2),
    )

    # --- 2. TABLA CON BARRAS VISUALES DE LENGUAJES (DERECHA) ---
    lang_stats = calculate_language_stats(repos_data)
    lang_table = Table(title="📊 Lenguajes Más Usados", expand=True)
    lang_table.add_column("Lenguaje", style="bold cyan")
    lang_table.add_column("Repos", justify="center", style="yellow")
    lang_table.add_column("Distribución", style="green")

    for item in lang_stats:
        # Crea una barrita gráfica con caracteres Unicode
        bars = "█" * int(item["percentage"] / 10)
        lang_table.add_row(
            item["language"],
            str(item["count"]),
            f"{bars} {item['percentage']:.1f}%",
        )

    # Imprimir perfil y estadísticas en columnas lado a lado
    console.print(Columns([profile_panel, lang_table]))
    console.print("\n")

    # --- 3. TABLA DE REPOSITORIOS RECIENTES ---
    repo_table = Table(
        title=f"🚀 Últimos {limit} Repositorios Actualizados", expand=True
    )
    repo_table.add_column("Nombre del Repositorio", style="bold blue", no_wrap=True)
    repo_table.add_column("Lenguaje", style="magenta")
    repo_table.add_column("⭐ Estrellas", justify="right", style="yellow")
    repo_table.add_column("🍴 Forks", justify="right", style="cyan")

    for repo in repos_data[:limit]:
        repo_table.add_row(
            repo.get("name"),
            repo.get("language") or "N/A",
            str(repo.get("stargazers_count", 0)),
            str(repo.get("forks_count", 0)),
        )

    console.print(repo_table)


# Permitir ejecución tanto con "gh-summary fetch USER" como con "gh-summary USER"
@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, username: str = None):
    if ctx.invoked_subcommand is None and username:
        fetch(username=username)


if __name__ == "__main__":
    app()