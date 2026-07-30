from collections import Counter


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

    md = [
        f"# 👤 Resumen de GitHub: {name} (@{username})\n",
        f"> {bio}\n",
        "## 📌 Información General\n",
        f"- **📍 Ubicación:** {user_data.get('location', 'N/A')}",
        f"- **👥 Seguidores:** {user_data.get('followers')} | **Siguiendo:** {user_data.get('following')}",
        f"- **📦 Repositorios Públicos:** {user_data.get('public_repos')}\n",
    ]

    if ai_summary_text:
        md.extend(
            ["## 🤖 Análisis Ejecutivo (Gemini AI)\n", f"{ai_summary_text}\n"]
        )

    md.append("## 📊 Lenguajes Más Usados\n")
    if lang_stats:
        md.append("| Lenguaje | Repositorios | Porcentaje |")
        md.append("| --- | --- | --- |")
        for item in lang_stats:
            md.append(
                f"| {item['language']} | {item['count']} | {item['percentage']:.1f}% |"
            )
        md.append("")
    else:
        md.append("_No hay suficientes datos de lenguajes._\n")

    md.append("## 🚀 Repositorios Recientes\n")
    md.append("| Repositorio | Lenguaje | ⭐ Estrellas | 🍴 Forks | Link |")
    md.append("| --- | --- | --- | --- | --- |")
    for repo in repos_data:
        r_name = repo.get("name")
        r_lang = repo.get("language") or "N/A"
        r_stars = repo.get("stargazers_count", 0)
        r_forks = repo.get("forks_count", 0)
        r_url = repo.get("html_url")
        md.append(
            f"| [{r_name}]({r_url}) | {r_lang} | {r_stars} | {r_forks} | [Ver Repo]({r_url}) |"
        )

    return "\n".join(md)