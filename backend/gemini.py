import json
import os
import time

import requests

# flash-lite : quota gratuit plus généreux (30 req/min, 1500 req/jour) que flash (20 req/min)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

MAX_RETRIES = 6  # 6 essais × ~10s = jusqu'à 60s d'attente pour passer le quota/min

_INSIGHT_SYSTEM_PROMPT = (
    "Tu es un analyste business expert. L'entreprise est une PME camerounaise du secteur électronique et électroménager. "
    "La devise est le FCFA (Franc CFA) et les montants sont en FCFA. "
    "Génère des insights courts (2-3 phrases maximum) en français "
    "pour aider le décideur à prendre une décision."
)


def _call_gemini(prompt: str) -> str:
    """Appel bas niveau à Gemini avec retry/backoff sur 429. Lève RuntimeError si échec."""
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set in environment variables.")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    headers = {"Content-Type": "application/json"}

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={gemini_api_key}",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if response.status_code == 429:
                # Sur 429, Gemini indique souvent "Please retry in Xs".
                # On attend le délai suggéré, sinon ~10s (pour passer le reset
                # du quota par minute), jusqu'à MAX_RETRIES essais.
                retry_after = response.headers.get("Retry-After")
                wait = float(retry_after) if retry_after else 10.0
                time.sleep(wait)
                last_error = "Rate limit (429) exceeded"
                continue

            response.raise_for_status()
            result = response.json()

            candidates = result.get("candidates") or []
            if (
                candidates
                and isinstance(candidates[0], dict)
                and "content" in candidates[0]
                and isinstance(candidates[0]["content"], dict)
                and "parts" in candidates[0]["content"]
                and candidates[0]["content"]["parts"]
                and "text" in candidates[0]["content"]["parts"][0]
            ):
                return candidates[0]["content"]["parts"][0]["text"].strip()

            return ""
        except requests.RequestException as exc:
            last_error = str(exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(10.0)
                continue
            raise RuntimeError(f"Gemini API request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError(f"Invalid response from Gemini API: {exc}") from exc

    raise RuntimeError(
        f"Gemini API request failed after {MAX_RETRIES} retries: {last_error}"
    )


def generate_insight(data: dict, context: str) -> str:
    """Génère un insight court en français à partir de données et d'un contexte (1 appel API)."""
    prompt = (
        f"{_INSIGHT_SYSTEM_PROMPT}\n\n"
        f"Voici les données : {data}\n"
        f"Contexte : {context}\n"
        "Réponds uniquement avec un objet JSON de la forme {\"insight\": \"...\"}."
    )
    try:
        raw = _call_gemini(prompt)
    except (EnvironmentError, RuntimeError):
        return ""

    try:
        parsed = json.loads(raw)
        return str(parsed.get("insight", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        # Si le JSON échoue, on retourne le texte brut (fallback robuste)
        return raw


def generate_insights_batch(specs: list[dict]) -> dict[str, str]:
    """
    Génère plusieurs insights en UN SEUL appel API.

    Args:
        specs: liste de dicts {key, data, context}.
    Returns:
        Dict {key: insight}. Les clés absentes de la réponse IA valent "".
    """
    if not specs:
        return {}

    items = "\n".join(
        f"- {s['key']} (contexte: {s['context']}) : {s['data']}"
        for s in specs
    )
    keys = [s["key"] for s in specs]
    prompt = (
        f"{_INSIGHT_SYSTEM_PROMPT}\n\n"
        f"Voici plusieurs jeux de données à analyser :\n{items}\n\n"
        f"Réponds uniquement avec un objet JSON de la forme "
        f'{{"{keys[0]}": "...", "{keys[1] if len(keys) > 1 else "autre"}": "..."}} '
        "contenant un insight court pour chaque clé listée ci-dessus."
    )
    try:
        raw = _call_gemini(prompt)
    except (EnvironmentError, RuntimeError):
        return {k: "" for k in keys}

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {k: str(parsed.get(k, "")).strip() for k in keys}
    except (json.JSONDecodeError, AttributeError):
        pass
    # Fallback : si la réponse n'est pas un JSON exploitable, on attribue
    # le texte brut à toutes les clés (moins idéal mais non bloquant)
    return {k: raw for k in keys}
