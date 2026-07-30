import asyncio
import json
from pathlib import Path
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from gh_summary.ai import generate_ai_summary
from gh_summary.api import fetch_github_data
from gh_summary.formatters import calculate_language_stats, format_as_markdown
from gh_summary.health import analyze_repo_health

app = typer.Typer(
    help="Herramienta CLI para obtener resúmenes visuales de perfiles de GitHub."
)
console = Console()


@app.command(name="fetch")
def fetch(
    username: str,
    limit: int = typer.Option(5, help="Número de repositorios a mostrar en la tabla."),
    ai_summary: bool = typer.Option(
        False,
        "--ai-summary",
        "-a",
        help="Genera un resumen narrativo con Gemini AI.",
    ),
    output_format: str = typer.Option(
        "terminal",
        "--format",
        "-f",
        help="Formato de salida: 'terminal' (interactivo), 'md' (Markdown) o 'json'.",
    ),
    output_file: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Ruta del archivo donde guardar la salida (ej. perfil.md).",
    ),
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

    lang_stats = calculate_language_stats(repos_data)
    repos_subset = repos_data[:limit]

    ai_text = None
    if ai_summary:
        with console.status(
            "[bold green]🤖 Generando análisis inteligente con Gemini AI...[/bold green]",
            spinner="dots",
        ):
            ai_text = generate_ai_summary(user_data, repos_data)

    # Manejo de exportaciones (Markdown / JSON)
    if output_format.lower() in ["md", "markdown"]:
        content = format_as_markdown(user_data, lang_stats, repos_subset, ai_text)
        if output_file:
            Path(output_file).write_text(content, encoding="utf-8")
            console.print(f"[bold green]✅ Informe exportado con éxito a:[/bold green] {output_file}")
        else:
            print(content)
        return

    elif output_format.lower() == "json":
        data = {
            "user": user_data,
            "language_stats": lang_stats,
            "recent_repos": repos_subset,
            "ai_summary": ai_text,
        }
        content = json.dumps(data, indent=2, ensure_ascii=False)
        if output_file:
            Path(output_file).write_text(content, encoding="utf-8")
            console.print(f"[bold green]✅ Datos JSON exportados con éxito a:[/bold green] {output_file}")
        else:
            print(content)
        return

    # Renderizado en Terminal (Rich Dashboard)
    console.clear()

    bio = user_data.get("bio") or "Sin biografía disponible."
    profile_text = (
        f"[bold white]{user_data.get('name', username)}[/bold white] (@{username})\n"
        f"[dim]{bio}[/dim]\n\n"
        f"📍 [cyan]Ubicación:[/cyan] {user_data.get('location', 'N/A')}\n"
        f"👥 [cyan]Seguidores:[/cyan] {user_data.get('followers')}  |  [cyan]Siguiendo:[/cyan] {user_data.get('following')}\n"
        f"📦 [cyan]Repositorios Públicos:[/cyan] {user_data.get('public_repos')}"
    )
    profile_panel = Panel(
        profile_text, title="👤 Perfil de GitHub", border_style="magenta", padding=(1, 2)
    )

    lang_table = Table(title="📊 Lenguajes Más Usados", expand=True)
    lang_table.add_column("Lenguaje", style="bold cyan")
    lang_table.add_column("Repos", justify="center", style="yellow")
    lang_table.add_column("Distribución", style="green")

    for item in lang_stats:
        bars = "█" * int(item["percentage"] / 10)
        lang_table.add_row(item["language"], str(item["count"]), f"{bars} {item['percentage']:.1f}%")

    console.print(Columns([profile_panel, lang_table]))
    console.print("\n")

    if ai_summary and ai_text:
        ai_panel = Panel(
            ai_text, title="🤖 Análisis Ejecutivo por Gemini AI", border_style="cyan", padding=(1, 2)
        )
        console.print(ai_panel)
        console.print("\n")

    repo_table = Table(title=f"🚀 Últimos {limit} Repositorios Actualizados", expand=True)
    repo_table.add_column("Nombre del Repositorio", style="bold blue", no_wrap=True)
    repo_table.add_column("Lenguaje", style="magenta")
    repo_table.add_column("⭐ Estrellas", justify="right", style="yellow")
    repo_table.add_column("🍴 Forks", justify="right", style="cyan")

    for repo in repos_subset:
        repo_table.add_row(
            repo.get("name"),
            repo.get("language") or "N/A",
            str(repo.get("stargazers_count", 0)),
            str(repo.get("forks_count", 0)),
        )

    console.print(repo_table)


@app.command(name="compare")
def compare(user1: str, user2: str):
    """Compara las métricas de dos usuarios de GitHub lado a lado."""
    async def fetch_both():
        return await asyncio.gather(
            fetch_github_data(user1), fetch_github_data(user2), return_exceptions=True
        )

    with console.status(
        f"[bold blue]Consultando perfiles de @{user1} y @{user2}...[/bold blue]", spinner="dots"
    ):
        results = asyncio.run(fetch_both())

    res1, res2 = results
    if isinstance(res1, Exception):
        console.print(f"[bold red]❌ Error obteniendo datos de @{user1}:[/bold red] {res1}")
        return
    if isinstance(res2, Exception):
        console.print(f"[bold red]❌ Error obteniendo datos de @{user2}:[/bold red] {res2}")
        return

    u1_data, u1_repos = res1
    u2_data, u2_repos = res2

    u1_langs = calculate_language_stats(u1_repos)
    u2_langs = calculate_language_stats(u2_repos)

    u1_main_lang = u1_langs[0]["language"] if u1_langs else "N/A"
    u2_main_lang = u2_langs[0]["language"] if u2_langs else "N/A"

    u1_stars = sum(r.get("stargazers_count", 0) for r in u1_repos)
    u2_stars = sum(r.get("stargazers_count", 0) for r in u2_repos)

    console.clear()

    table = Table(
        title=f"⚔️ Comparativa Directa: @{user1} vs @{user2}",
        expand=True,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Métrica / Atributo", style="cyan", no_wrap=True)
    table.add_column(f"👤 {u1_data.get('name', user1)} (@{user1})", justify="center", style="bold white")
    table.add_column(f"👤 {u2_data.get('name', user2)} (@{user2})", justify="center", style="bold white")

    followers_u1 = f"[green]{u1_data.get('followers')}[/green]" if u1_data.get('followers') > u2_data.get('followers') else str(u1_data.get('followers'))
    followers_u2 = f"[green]{u2_data.get('followers')}[/green]" if u2_data.get('followers') > u1_data.get('followers') else str(u2_data.get('followers'))

    repos_u1 = f"[green]{u1_data.get('public_repos')}[/green]" if u1_data.get('public_repos') > u2_data.get('public_repos') else str(u1_data.get('public_repos'))
    repos_u2 = f"[green]{u2_data.get('public_repos')}[/green]" if u2_data.get('public_repos') > u1_data.get('public_repos') else str(u2_data.get('public_repos'))

    stars_u1 = f"[green]⭐ {u1_stars}[/green]" if u1_stars > u2_stars else f"⭐ {u1_stars}"
    stars_u2 = f"[green]⭐ {u2_stars}[/green]" if u2_stars > u1_stars else f"⭐ {u2_stars}"

    table.add_row("Ubicación", str(u1_data.get('location', 'N/A')), str(u2_data.get('location', 'N/A')))
    table.add_row("Seguidores", followers_u1, followers_u2)
    table.add_row("Siguiendo", str(u1_data.get('following')), str(u2_data.get('following')))
    table.add_row("Repositorios Públicos", repos_u1, repos_u2)
    table.add_row("Estrellas Totales (Muestra)", stars_u1, stars_u2)
    table.add_row("Lenguaje Principal", f"[yellow]{u1_main_lang}[/yellow]", f"[yellow]{u2_main_lang}[/yellow]")

    console.print(table)


@app.command(name="health")
def health(username: str):
    """Audita la salud de los repositorios públicos de un usuario."""
    with console.status(
        f"[bold blue]Auditando repositorios de @{username}...[/bold blue]", spinner="dots"
    ):
        try:
            _, repos_data = asyncio.run(fetch_github_data(username))
        except Exception as e:
            console.print(f"[bold red]❌ Error de conexión:[/bold red] {e}")
            return

    health_info = analyze_repo_health(repos_data)
    score = health_info["score"]

    console.clear()

    score_color = "bold green" if score >= 80 else ("bold yellow" if score >= 50 else "bold red")

    summary_text = (
        f"🏥 [bold white]Puntuación General de Salud:[/bold white] [{score_color}]{score} / 100[/{score_color}]\n\n"
        f"📊 [cyan]Muestra de repositorios auditados:[/cyan] {health_info['total']}\n"
        f"📝 [cyan]Con descripción:[/cyan] {health_info['has_description']} / {health_info['total']}\n"
        f"📜 [cyan]Con licencia válida:[/cyan] {health_info['has_license']} / {health_info['total']}\n"
        f"⚡ [cyan]Activos en el último año:[/cyan] {health_info['recently_updated']} / {health_info['total']}"
    )

    console.print(Panel(summary_text, title=f"🩺 Reporte de Salud: @{username}", border_style="green", padding=(1, 2)))
    console.print("\n")

    table = Table(title="🔍 Detalle por Repositorio Auditado", expand=True)
    table.add_column("Repositorio", style="bold blue")
    table.add_column("Descripción", justify="center")
    table.add_column("Licencia", justify="center")
    table.add_column("Activo (12 meses)", justify="center")

    for repo in health_info["repos_audit"]:
        table.add_row(
            repo["name"],
            "✅" if repo["has_description"] else "❌",
            "✅" if repo["has_license"] else "❌",
            "⚡ Sí" if repo["is_active"] else "💤 Inactivo",
        )

    console.print(table)
    console.print("\n")

    if health_info["issues"]:
        console.print(
            Panel("\n".join(health_info["issues"]), title="💡 Recomendaciones de Mejora", border_style="yellow", padding=(1, 2))
        )


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, username: str = None):
    if ctx.invoked_subcommand is None and username:
        fetch(username=username)


if __name__ == "__main__":
    app()