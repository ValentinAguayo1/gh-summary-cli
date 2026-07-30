from collections import Counter
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

app = typer.Typer(
    help="Herramienta CLI para obtener resumenes visuales de perfiles de GitHub."
)
console = Console()


def calculate_language_stats(repos_data: list) -> list:
    """Calcula la frecuencia de los lenguajes principales en una lista de repositorios."""
    languages = [repo.get("language") for repo in repos_data if repo.get("language")]
    if not languages:
        return []
    
    total_langs = len(languages)
    lang_counts = Counter(languages)
    
    stats = []
    for lang, count in lang_counts.most_common(3):
        pct = (count / total_langs) * 100
        stats.append({"language": lang, "count": count, "percentage": pct})
    return stats


@app.command(name="fetch")
def fetch(username: str, limit: int = typer.Option(5, help="Numero de repositorios a mostrar.")):
    """Obtiene y muestra informacion detallada de un usuario de GitHub."""
    console.print(
        f"\n[bold blue]Buscando datos para:[/bold blue] [cyan]{username}[/cyan]..."
    )

    url_user = f"https://api.github.com/users/{username}"
    url_repos = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100"

    try:
        with httpx.Client() as client:
            res_user = client.get(url_user)
            res_repos = client.get(url_repos)

        if res_user.status_code == 404:
            console.print(
                f"[bold red]Error: El usuario '{username}' no existe en GitHub.[/bold red]"
            )
            return

        user_data = res_user.json()
        repos_data = res_repos.json()

        # 1. Panel de Informacion Principal
        profile_info = (
            f"[bold]{user_data.get('name', username)}[/bold]\n"
            f"[italic]{user_data.get('bio', 'Sin biografia disponible.')}[/italic]\n\n"
            f"Ubicacion: {user_data.get('location', 'N/A')}\n"
            f"Seguidores: {user_data.get('followers')} | Siguiendo: {user_data.get('following')}\n"
            f"Repositorios Publicos: {user_data.get('public_repos')}"
        )

        console.print(
            Panel(
                profile_info,
                title=f"Perfil de GitHub - @{username}",
                expand=False,
                border_style="green",
            )
        )

        # 2. Estadisticas de Lenguajes
        lang_stats = calculate_language_stats(repos_data)
        if lang_stats:
            lang_table = Table(title="Distribucion de Lenguajes")
            lang_table.add_column("Lenguaje", style="cyan")
            lang_table.add_column("Uso", style="magenta")
            lang_table.add_column("Porcentaje", style="green", justify="right")

            for item in lang_stats:
                lang_table.add_row(
                    item["language"], 
                    f"{item['count']} repos", 
                    f"{item['percentage']:.1f}%"
                )

            console.print(lang_table)

        # 3. Tabla de Repositorios
        table = Table(title=f"Ultimos {limit} Repositorios Actualizados")
        table.add_column("Nombre", style="cyan", no_wrap=True)
        table.add_column("Lenguaje", style="magenta")
        table.add_column("Estrellas", style="yellow", justify="right")

        for repo in repos_data[:limit]:
            table.add_row(
                repo.get("name"),
                repo.get("language") or "N/A",
                str(repo.get("stargazers_count", 0)),
            )

        console.print(table)

    except Exception as e:
        console.print(
            f"[bold red]Ocurrio un error al conectar con GitHub:[/bold red] {e}"
        )


if __name__ == "__main__":
    app()