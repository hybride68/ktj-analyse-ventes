import os
import requests

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

def generate_insight(data: dict, context: str) -> str:
    """Generate a short business insight in French from provided data and context."""
    if not GEMINI_API_KEY:
        raise EnvironmentError("GEMINI_API_KEY is not set in environment variables.")

    prompt = (
        "Tu es un analyste business expert. L'entreprise est une PME camerounaise du secteur électronique et électroménager. "
        "La devise est le FCFA (Franc CFA) et les montants sont en FCFA. "
        "Voici les données : "
        f"{data}. Contexte : {context}. "
        "Génère un insight court (2-3 phrases maximum) en français "
        "pour aider le décideur à prendre une décision."
    )

    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        result = response.json()

        if (
            "candidates" in result
            and isinstance(result["candidates"], list)
            and result["candidates"]
            and isinstance(result["candidates"][0], dict)
            and "content" in result["candidates"][0]
            and isinstance(result["candidates"][0]["content"], dict)
            and "parts" in result["candidates"][0]["content"]
            and isinstance(result["candidates"][0]["content"]["parts"], list)
            and result["candidates"][0]["content"]["parts"]
            and "text" in result["candidates"][0]["content"]["parts"][0]
        ):
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()

        return ""
    except requests.RequestException as exc:
        raise RuntimeError(f"Gemini API request failed: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(f"Invalid response from Gemini API: {exc}") from exc
