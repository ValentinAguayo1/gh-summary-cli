from collections import Counter
from datetime import datetime, timezone


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


def format_compact_number(value: int) -> str:
    """Formatea números grandes de forma legible (ej. 12500 -> 12.5k)."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def format_progress_bar(percentage: float, width: int = 15) -> str:
    """Genera una barra de progreso ASCII proporcional al porcentaje."""
    filled = round((percentage / 100) * width)
    filled = min(max(filled, 0), width)
    return "█" * filled + "░" * (width - filled)


def format_ratio_bar(current: int, total: int, width: int = 16) -> str:
    """Barra de progreso con contador y porcentaje (ej. auditoría de salud)."""
    if total == 0:
        return f"{'░' * width} 0/0 (0%)"
    pct = (current / total) * 100
    return f"{format_progress_bar(pct, width)} {current}/{total} ({pct:.0f}%)"


def format_relative_date(iso_date: str | None) -> str:
    """Convierte una fecha ISO de GitHub a texto relativo en español."""
    if not iso_date:
        return "N/A"
    updated = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - updated).days
    if days == 0:
        return "hoy"
    if days == 1:
        return "ayer"
    if days < 30:
        return f"hace {days} d"
    if days < 365:
        months = days // 30
        return f"hace {months} mes" if months == 1 else f"hace {months} meses"
    years = days // 365
    return f"hace {years} año" if years == 1 else f"hace {years} años"


def format_as_markdown(
    user_data: dict,
    lang_stats: list,
    repos_data: list,
    ai_summary_text: str = None,
) -> str:
    """Genera un informe estructurado en formato Markdown impecable."""
    username = user_data.get("login")
    name = user_data.get("name") or username
    bio = user_data.get("bio") or "Sin biografía disponible."
    profile_url = user_data.get("html_url") or f"https://github.com/{username}"

    md = [
        f"# 👤 Resumen de GitHub: {name} (@{username})\n",
        f"> {bio}\n",
        f"🔗 [Ver perfil en GitHub]({profile_url})\n",
        "## 📌 Información General\n",
        f"- **📍 Ubicación:** {user_data.get('location', 'N/A')}",
        f"- **👥 Seguidores:** {format_compact_number(user_data.get('followers', 0))} | **Siguiendo:** {format_compact_number(user_data.get('following', 0))}",
        f"- **📦 Repositorios Públicos:** {user_data.get('public_repos')}\n",
    ]

    if ai_summary_text:
        md.extend(
            ["## 🤖 Análisis Ejecutivo (Gemini AI)\n", f"{ai_summary_text}\n"]
        )

    md.append("## 📊 Lenguajes Más Usados\n")
    if lang_stats:
        md.append("| Lenguaje | Repositorios | Porcentaje |")
        md.append("| --- | ---: | ---: |")
        for item in lang_stats:
            md.append(
                f"| {item['language']} | {item['count']} | {item['percentage']:.1f}% |"
            )
        md.append("")
    else:
        md.append("_No hay suficientes datos de lenguajes._\n")

    md.append("## 🚀 Repositorios Recientes\n")
    if repos_data:
        md.append("| Repositorio | Lenguaje | ⭐ Estrellas | 🍴 Forks | Actualizado |")
        md.append("| --- | --- | ---: | ---: | ---: |")
        for repo in repos_data:
            r_name = repo.get("name")
            r_lang = repo.get("language") or "N/A"
            r_stars = format_compact_number(repo.get("stargazers_count", 0))
            r_forks = format_compact_number(repo.get("forks_count", 0))
            r_updated = format_relative_date(repo.get("updated_at"))
            r_url = repo.get("html_url")
            md.append(
                f"| [{r_name}]({r_url}) | {r_lang} | {r_stars} | {r_forks} | {r_updated} |"
            )
    else:
        md.append("_No hay repositorios públicos para mostrar._\n")

    return "\n".join(md)
