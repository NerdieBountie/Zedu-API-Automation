"""
utils/auth.py
─────────────
Single source of truth for authentication against the Zedu API.

ALL token acquisition logic lives here.  No test file ever calls
/auth/login directly or stores a token literal.

Public API
──────────
  get_base_url()          → str
  login(email, password)  → requests.Response
  get_auth_token(...)     → str   (raises ValueError on failure)
  auth_headers(...)       → dict  {"Authorization": "Bearer <token>"}
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


def get_base_url() -> str:
    """Return the API base URL, stripped of trailing slashes."""
    url = os.getenv("BASE_URL", "https://api.zedu.chat")
    return url.rstrip("/")


def login(email: str = None, password: str = None) -> requests.Response:
    """
    POST /auth/login with the supplied (or env-default) credentials.

    Parameters
    ----------
    email    : str | None  — falls back to TEST_EMAIL env var
    password : str | None  — falls back to TEST_PASSWORD env var

    Returns
    -------
    requests.Response  — caller decides what to do with status / body
    """
    payload = {
        "email": email or os.getenv("TEST_EMAIL"),
        "password": password or os.getenv("TEST_PASSWORD"),
    }
    return requests.post(f"{get_base_url()}/auth/login", json=payload)


def get_auth_token(email: str = None, password: str = None) -> str:
    """
    Log in and return the raw token string.

    The Zedu API wraps responses in a `data` envelope, e.g.:
        { "status": "success", "data": { "token": "..." } }

    We probe several common shapes so the helper survives minor
    API changes without touching every test file.

    Raises
    ------
    ValueError  – if login fails or no token can be located
    """
    response = login(email, password)
    if response.status_code != 200:
        raise ValueError(
            f"Login failed (HTTP {response.status_code}): {response.text}"
        )
    body = response.json()

    # Try common token key paths (most → least specific)
    token = (
        # Zedu envelope shape: { data: { token | access_token } }
        (body.get("data") or {}).get("token")
        or (body.get("data") or {}).get("access_token")
        # Flat shape: { token | access_token }
        or body.get("token")
        or body.get("access_token")
    )

    if not token:
        raise ValueError(f"Token not found in login response: {body}")
    return token


def auth_headers(email: str = None, password: str = None) -> dict:
    """
    Return ready-to-use Authorization headers.

    Usage:
        response = requests.get(url, headers=auth_headers())
    """
    return {"Authorization": f"Bearer {get_auth_token(email, password)}"}
