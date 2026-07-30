import os
from google import genai

def generate_ai_summary(user_data: dict, repos_data: list) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ Variable GEMINI_API_KEY no configurada."

    client = genai.Client(api_key=api_key)
    repo_names = [r.get("name") for r in repos_data[:5]]
    languages = list(set(r.get("language") for r in repos_data if r.get("language")))

    prompt = f"""
    Eres un analista técnico. Genera un resumen ejecutivo breve (máximo 3 oraciones) 
    sobre el perfil del desarrollador {user_data.get('name', 'Usuario')}.
    
    Datos:
    - Biografía: {user_data.get('bio', 'Sin biografía')}
    - Repositorios públicos: {user_data.get('public_repos')}
    - Lenguajes: {', '.join(languages)}
    - Repos recientes: {', '.join(repo_names)}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return f"Error al comunicarse con Gemini AI: {e}"