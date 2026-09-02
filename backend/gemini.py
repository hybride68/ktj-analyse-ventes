import ast
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / "backend" / ".env")
load_dotenv(_PROJECT_ROOT / ".env")

# flash-lite : quota gratuit plus généreux (30 req/min, 1500 req/jour) que flash (20 req/min)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

MAX_RETRIES = 6  # 6 essais × ~10s = jusqu'à 60s d'attente pour passer le quota/min

_INSIGHT_SYSTEM_PROMPT = (
    "Tu es un analyste business expert. L'entreprise est une PME camerounaise du secteur électronique et électroménager. "
    "La devise est le FCFA (Franc CFA) et les montants sont en FCFA. "
    "Analyse uniquement les données fournies, sans inventer de valeur. "
    "Génère des insights courts mais explicatifs (3-5 phrases maximum) en français. "
    "Chaque insight doit citer au moins un chiffre ou une comparaison présente dans les données, "
    "expliquer ce que cela signifie pour l'activité, puis proposer une action concrète. "
    "Si les données sont insuffisantes, dis précisément quelle information manque."
)


def _money(value) -> str:
    try:
        return f"{float(value):,.0f} FCFA"
    except (TypeError, ValueError):
        return str(value)


def _fallback_insight(key: str, data: list[dict] | dict | None, context: str = "") -> str:
    """Fournit un message simple et utile sans dépendre de Gemini."""
    if not data:
        return "Aucune donnée disponible pour générer un insight fiable."

    if key == "monthly":
        records = data if isinstance(data, list) else []
        if not records:
            return "La série mensuelle est vide, il faut vérifier la disponibilité des données."
        values = []
        for item in records:
            try:
                values.append(float(item.get("ca_total", 0)))
            except (TypeError, ValueError):
                continue
        if len(values) < 2:
            return f"Le CA mensuel actuel est de {_money(values[-1])} pour la période observée."
        last = values[-1]
        prev = values[-2]
        delta = last - prev
        direction = "hausse" if delta >= 0 else "baisse"
        return (
            f"Le CA mensuel affiche une {direction} de {_money(abs(delta))} entre les deux derniers mois, "
            f"avec un niveau actuel de {_money(last)}."
        )

    if key == "boutique":
        records = data if isinstance(data, list) else []
        if not records:
            return "Les performances par boutique sont introuvables pour l'instant."
        best = max(records, key=lambda x: float(x.get("ca_total", 0)))
        worst = min(records, key=lambda x: float(x.get("ca_total", 0)))
        return (
            f"La boutique {best.get('id_boutique', 'principale')} est la meilleure avec {_money(best.get('ca_total', 0))}, "
            f"tandis que {worst.get('id_boutique', 'la moins performante')} arrive en queue avec {_money(worst.get('ca_total', 0))}."
        )

    if key == "paiement":
        records = data if isinstance(data, list) else []
        if not records:
            return "Aucune donnée de paiement n'est disponible pour analyser le mix de paiement."
        best = max(records, key=lambda x: float(x.get("ca_total", 0)))
        return (
            f"Le mode de paiement {best.get('mode_paiement', 'principal')} domine le CA avec {_money(best.get('ca_total', 0))}."
        )

    if isinstance(data, list) and data:
        total = sum(float(item.get("ca_total", 0)) for item in data if isinstance(item, dict))
        return f"Le niveau observé sur cette vue est de {_money(total)} de CA, ce qui justifie un suivi renforcé."

    return f"Le contexte {context or key} est exploitable, mais il manque encore des éléments pour un diagnostic plus fin."


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


def _parse_structured_response(raw: str) -> dict:
    """Accepte le JSON strict et le dictionnaire Python parfois renvoyé par Gemini."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").removeprefix("json").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        try:
            parsed = ast.literal_eval(cleaned)
        except (ValueError, SyntaxError):
            return {}
    return parsed if isinstance(parsed, dict) else {}


def generate_insight(data: dict, context: str) -> str:
    """Génère un insight court en français à partir de données et d'un contexte (1 appel API)."""
    prompt = (
        f"{_INSIGHT_SYSTEM_PROMPT}\n\n"
        f"Contexte métier : {context}\n"
        f"Données structurées à analyser : {json.dumps(data, ensure_ascii=False, default=str)}\n"
        "Réponds uniquement avec un objet JSON de la forme "
        "{\"insight\": \"constat chiffré ; explication ; action recommandée\"}."
    )
    try:
        raw = _call_gemini(prompt)
    except (EnvironmentError, RuntimeError):
        return _fallback_insight("general", data, context)

    parsed = _parse_structured_response(raw)
    insight = str(parsed.get("insight", "")).strip()
    return insight or _fallback_insight("general", data, context)


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
        f"- Clé: {s['key']}\n  Contexte: {s['context']}\n  Données: "
        f"{json.dumps(s['data'], ensure_ascii=False, default=str)}"
        for s in specs
    )
    keys = [s["key"] for s in specs]
    prompt = (
        f"{_INSIGHT_SYSTEM_PROMPT}\n\n"
        f"Voici plusieurs jeux de données à analyser :\n{items}\n\n"
        "Pour chaque clé, réponds uniquement avec un insight de 3 à 5 phrases qui contient "
        "un constat chiffré, une explication et une action concrète. "
        "N'invente aucune donnée. Retourne uniquement un objet JSON dont les clés sont exactement : "
        f"{json.dumps(keys, ensure_ascii=False)}."
    )
    try:
        raw = _call_gemini(prompt)
    except (EnvironmentError, RuntimeError):
        return {k: _fallback_insight(k, next((s["data"] for s in specs if s.get("key") == k), []), next((s["context"] for s in specs if s.get("key") == k), "")) for k in keys}

    parsed = _parse_structured_response(raw)
    return {
        k: str(parsed.get(k, "")).strip()
        or _fallback_insight(
            k,
            next((s["data"] for s in specs if s.get("key") == k), []),
            next((s["context"] for s in specs if s.get("key") == k), ""),
        )
        for k in keys
    }
