import asyncio
import json
from enum import Enum
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from gh_summary.ai import generate_ai_summary
from gh_summary.api import fetch_github_data
from gh_summary.formatters import (
    calculate_language_stats,
    format_as_markdown,
    format_compact_number,
    format_progress_bar,
    format_ratio_bar,
    format_relative_date,
)
from gh_summary.health import analyze_repo_health

app = typer.Typer(
    help="Herramienta CLI para obtener resúmenes visuales de perfiles de GitHub."
)
console = Console()


class OutputFormat(str, Enum):
    terminal = "terminal"
    md = "md"
    markdown = "markdown"
    json = "json"


def _fail(message: str) -> None:
    console.print(message)
    raise typer.Exit(1)


def _table(title: str) -> Table:
    return Table(title=title, expand=True, box=box.ROUNDED, show_header=True, header_style="bold")


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
    output_format: OutputFormat = typer.Option(
        OutputFormat.terminal,
        "--format",
        "-f",
        case_sensitive=False,
        help="Formato de salida: terminal, md o json.",
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
            _fail(f"[bold red]❌ Error:[/bold red] {err}")
        except Exception as e:
            _fail(f"[bold red]❌ Error de conexión:[/bold red] {e}")

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
    if output_format in (OutputFormat.md, OutputFormat.markdown):
        content = format_as_markdown(user_data, lang_stats, repos_subset, ai_text)
        if output_file:
            Path(output_file).write_text(content, encoding="utf-8")
            console.print(f"[bold green]✅ Informe exportado con éxito a:[/bold green] {output_file}")
        else:
            print(content)
        return

    elif output_format == OutputFormat.json:
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
    profile_url = user_data.get("html_url") or f"https://github.com/{username}"
    bio = user_data.get("bio") or "Sin biografía disponible."
    followers = format_compact_number(user_data.get("followers", 0))
    following = format_compact_number(user_data.get("following", 0))

    profile_text = (
        f"[bold white]{user_data.get('name', username)}[/bold white] (@{username})\n"
        f"[dim]{bio}[/dim]\n\n"
        f"📍 [cyan]Ubicación:[/cyan] {user_data.get('location', 'N/A')}\n"
        f"👥 [cyan]Seguidores:[/cyan] {followers}  |  [cyan]Siguiendo:[/cyan] {following}\n"
        f"📦 [cyan]Repositorios Públicos:[/cyan] {user_data.get('public_repos')}\n"
        f"🔗 [link={profile_url}]Abrir perfil en GitHub[/link]"
    )
    profile_panel = Panel(
        profile_text, title="👤 Perfil de GitHub", border_style="magenta", padding=(1, 2)
    )

    console.print()
    console.print(profile_panel)
    console.print(Rule(style="dim"))

    lang_table = _table("📊 Lenguajes Más Usados")
    lang_table.add_column("Lenguaje", style="bold cyan", no_wrap=True)
    lang_table.add_column("Repos", justify="right", style="yellow", width=6)
    lang_table.add_column("Distribución", style="green")

    if lang_stats:
        for item in lang_stats:
            bar = format_progress_bar(item["percentage"])
            lang_table.add_row(
                item["language"],
                str(item["count"]),
                f"{bar} {item['percentage']:.1f}%",
            )
    else:
        lang_table.add_row("[dim]Sin datos[/dim]", "—", "[dim]No hay lenguajes detectados[/dim]")

    console.print(lang_table)

    if ai_summary and ai_text:
        console.print(Rule(style="dim"))
        ai_panel = Panel(
            ai_text, title="🤖 Análisis Ejecutivo por Gemini AI", border_style="cyan", padding=(1, 2)
        )
        console.print(ai_panel)

    console.print(Rule(style="dim"))

    repo_table = _table(f"🚀 Últimos {limit} Repositorios Actualizados")
    repo_table.add_column("Repositorio", style="bold blue", no_wrap=True)
    repo_table.add_column("Lenguaje", style="magenta", width=12)
    repo_table.add_column("⭐", justify="right", style="yellow", width=6)
    repo_table.add_column("🍴", justify="right", style="cyan", width=6)
    repo_table.add_column("Actualizado", style="dim", width=14)

    for repo in repos_subset:
        repo_url = repo.get("html_url", "")
        repo_name = repo.get("name", "N/A")
        name_cell = f"[link={repo_url}]{repo_name}[/link]" if repo_url else repo_name
        repo_table.add_row(
            name_cell,
            repo.get("language") or "N/A",
            format_compact_number(repo.get("stargazers_count", 0)),
            format_compact_number(repo.get("forks_count", 0)),
            format_relative_date(repo.get("updated_at")),
        )

    console.print(repo_table)
    console.print()


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
        _fail(f"[bold red]❌ Error obteniendo datos de @{user1}:[/bold red] {res1}")
    if isinstance(res2, Exception):
        _fail(f"[bold red]❌ Error obteniendo datos de @{user2}:[/bold red] {res2}")

    u1_data, u1_repos = res1
    u2_data, u2_repos = res2

    u1_langs = calculate_language_stats(u1_repos)
    u2_langs = calculate_language_stats(u2_repos)

    u1_main_lang = u1_langs[0]["language"] if u1_langs else "N/A"
    u2_main_lang = u2_langs[0]["language"] if u2_langs else "N/A"

    u1_stars = sum(r.get("stargazers_count", 0) for r in u1_repos)
    u2_stars = sum(r.get("stargazers_count", 0) for r in u2_repos)

    def winner_cell(left, right, fmt=str):
        left_val = fmt(left)
        right_val = fmt(right)
        if left > right:
            return f"[bold green]{left_val}[/bold green]", str(right_val)
        if right > left:
            return str(left_val), f"[bold green]{right_val}[/bold green]"
        return str(left_val), str(right_val)

    console.print()

    table = _table(f"⚔️ Comparativa Directa: @{user1} vs @{user2}")
    table.add_column("Métrica / Atributo", style="cyan", no_wrap=True)
    table.add_column(f"👤 {u1_data.get('name', user1)} (@{user1})", justify="center", style="bold white")
    table.add_column(f"👤 {u2_data.get('name', user2)} (@{user2})", justify="center", style="bold white")

    followers_u1, followers_u2 = winner_cell(
        u1_data.get("followers", 0), u2_data.get("followers", 0), format_compact_number
    )
    repos_u1, repos_u2 = winner_cell(
        u1_data.get("public_repos", 0), u2_data.get("public_repos", 0)
    )
    stars_u1, stars_u2 = winner_cell(u1_stars, u2_stars, lambda n: f"⭐ {format_compact_number(n)}")

    table.add_row("Ubicación", str(u1_data.get("location", "N/A")), str(u2_data.get("location", "N/A")))
    table.add_row("Seguidores", followers_u1, followers_u2)
    table.add_row(
        "Siguiendo",
        format_compact_number(u1_data.get("following", 0)),
        format_compact_number(u2_data.get("following", 0)),
    )
    table.add_row("Repositorios Públicos", repos_u1, repos_u2)
    table.add_row("Estrellas Totales (Muestra)", stars_u1, stars_u2)
    table.add_row("Lenguaje Principal", f"[yellow]{u1_main_lang}[/yellow]", f"[yellow]{u2_main_lang}[/yellow]")

    console.print(table)
    console.print()


@app.command(name="health")
def health(username: str):
    """Audita la salud de los repositorios públicos de un usuario."""
    with console.status(
        f"[bold blue]Auditando repositorios de @{username}...[/bold blue]", spinner="dots"
    ):
        try:
            _, repos_data = asyncio.run(fetch_github_data(username))
        except ValueError as err:
            _fail(f"[bold red]❌ Error:[/bold red] {err}")
        except Exception as e:
            _fail(f"[bold red]❌ Error de conexión:[/bold red] {e}")

    health_info = analyze_repo_health(repos_data)
    score = health_info["score"]
    total = health_info["total"]

    console.print()

    score_color = "bold green" if score >= 80 else ("bold yellow" if score >= 50 else "bold red")
    score_bar = format_progress_bar(score, width=20)

    summary_text = (
        f"🏥 [bold white]Puntuación General de Salud:[/bold white] "
        f"[{score_color}]{score} / 100[/{score_color}]\n"
        f"[dim]{score_bar}[/dim]\n\n"
        f"📊 [cyan]Repositorios auditados:[/cyan] {total}\n"
        f"📝 [cyan]Con descripción:[/cyan] {format_ratio_bar(health_info['has_description'], total)}\n"
        f"📜 [cyan]Con licencia válida:[/cyan] {format_ratio_bar(health_info['has_license'], total)}\n"
        f"⚡ [cyan]Activos en el último año:[/cyan] {format_ratio_bar(health_info['recently_updated'], total)}"
    )

    console.print(
        Panel(
            summary_text,
            title=f"🩺 Reporte de Salud: @{username}",
            border_style="green",
            padding=(1, 2),
        )
    )
    console.print(Rule(style="dim"))

    table = _table("🔍 Detalle por Repositorio Auditado")
    table.add_column("Repositorio", style="bold blue", no_wrap=True)
    table.add_column("Descripción", justify="center", width=12)
    table.add_column("Licencia", justify="center", width=10)
    table.add_column("Actividad", justify="center", width=14)

    for repo in health_info["repos_audit"]:
        table.add_row(
            repo["name"],
            "[green]✅ Sí[/green]" if repo["has_description"] else "[red]❌ No[/red]",
            "[green]✅ Sí[/green]" if repo["has_license"] else "[red]❌ No[/red]",
            "[green]⚡ Activo[/green]" if repo["is_active"] else "[dim]💤 Inactivo[/dim]",
        )

    console.print(table)

    if health_info["issues"]:
        console.print(Rule(style="dim"))
        console.print(
            Panel(
                "\n".join(health_info["issues"]),
                title="💡 Recomendaciones de Mejora",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    console.print()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(0)


if __name__ == "__main__":
    app()
