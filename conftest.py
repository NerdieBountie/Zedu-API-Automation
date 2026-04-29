"""
conftest.py
───────────
Shared pytest fixtures for the entire Zedu API test suite.

Token acquisition happens ONLY here (via utils.auth).
Test files consume fixtures; they never call /auth/login themselves.
"""

import os
import uuid
import pytest
import requests
from faker import Faker
from dotenv import load_dotenv

from utils.auth import get_base_url, get_auth_token, login

load_dotenv()
fake = Faker()


# ── Base URL ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url() -> str:
    """Session-wide base URL from .env."""
    return get_base_url()


# ── Auth token & headers ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def valid_token() -> str:
    """
    Valid JWT obtained once per test session.
    Shared across all tests that need a good token.
    """
    return get_auth_token()


@pytest.fixture(scope="session")
def valid_headers(valid_token) -> dict:
    """Standard Authorization headers using a valid token."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture
def no_auth_headers() -> dict:
    """No Authorization header — probes unauthenticated access."""
    return {}


@pytest.fixture
def malformed_token_headers() -> dict:
    """A header whose token value is syntactically broken."""
    return {"Authorization": "Bearer not.a.real.jwt.at.all"}


@pytest.fixture
def expired_token_headers() -> dict:
    """
    A well-formed but expired/revoked token.
    Value read from EXPIRED_TOKEN env var; falls back to a static
    expired example JWT so tests still run without manual setup.
    """
    token = os.getenv(
        "EXPIRED_TOKEN",
        (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
            ".eyJzdWIiOiIwMDAwMDAwMCIsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjoxNTE2MjM5MDIyfQ"
            ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ),
    )
    return {"Authorization": f"Bearer {token}"}


# ── Dynamic data factories ────────────────────────────────────────────────────

@pytest.fixture
def unique_email() -> str:
    """Brand-new unique email address for each test invocation."""
    return f"qa_{uuid.uuid4().hex[:10]}@testmail.invalid"


@pytest.fixture
def unique_username() -> str:
    """Brand-new unique username for each test invocation."""
    return f"qauser_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def valid_register_payload(unique_email, unique_username) -> dict:
    """
    A complete, valid registration body using dynamic values.
    Adjust field names if the Zedu /auth/register schema differs.
    """
    return {
        "email": unique_email,
        "username": unique_username,
        "password": "Test@Secure1234!",
        "firstName": fake.first_name(),
        "lastName": fake.last_name(),
    }


# ── Shared HTTP session ───────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def api_session() -> requests.Session:
    """Reusable requests.Session with JSON content-type set."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
