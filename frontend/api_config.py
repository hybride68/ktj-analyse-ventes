import os


def get_api_url(default: str = "http://127.0.0.1:8000") -> str:
    raw_value = (os.getenv("API_URL") or os.getenv("BACKEND_URL") or "").strip()
    if raw_value:
        return raw_value.rstrip("/")
    return default
