"""
tests/test_auth.py
──────────────────
Tests for Zedu authentication endpoints:
  POST /auth/register
  POST /auth/login
  POST /auth/logout
  POST /auth/password-reset
  GET  /auth/onboard-status

Positive  : 5
Negative  : 8
Edge      : 3
Total     : 16
"""

import uuid
import os
import pytest
import requests
from dotenv import load_dotenv
from utils.auth import get_base_url, login

load_dotenv()
BASE = get_base_url()


# ─── helpers ────────────────────────────────────────────────────────────────

def _register(email: str, password: str = "Test@Secure1234!",
              username: str = None, first_name: str = "QA",
              last_name: str = "Tester") -> requests.Response:
    """Call POST /auth/register without needing a fixture."""
    return requests.post(
        f"{BASE}/auth/register",
        json={
            "email": email,
            "username": username or f"u_{uuid.uuid4().hex[:8]}",
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
        },
    )


def _extract_token(response: requests.Response) -> str | None:
    """Pull token from Zedu's envelope shape: { data: { token } }."""
    body = response.json()
    return (
        (body.get("data") or {}).get("token")
        or (body.get("data") or {}).get("access_token")
        or body.get("token")
        or body.get("access_token")
    )


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginPositive:

    def test_valid_credentials_returns_200(self):
        """POST /auth/login with correct creds must return 200."""
        response = login()
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_login_response_contains_token(self):
        """Successful login body must include a token field."""
        response = login()
        assert response.status_code == 200
        token = _extract_token(response)
        assert token is not None, (
            f"No token key found in response: {response.json()}"
        )

    def test_login_token_is_non_empty_string(self):
        """Token value must be a non-empty string."""
        response = login()
        assert response.status_code == 200
        token = _extract_token(response)
        assert isinstance(token, str)
        assert len(token) > 20, "Token seems too short to be a real JWT"

    def test_login_response_content_type_is_json(self):
        """Response Content-Type must be application/json."""
        response = login()
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_login_response_body_is_valid_json(self):
        """Response body must be parseable as JSON (no parse errors)."""
        response = login()
        assert response.status_code == 200
        try:
            body = response.json()
            assert isinstance(body, dict)
        except Exception as exc:
            pytest.fail(f"Response body is not valid JSON: {exc}")


# ═══════════════════════════════════════════════════════════════════════════════
# NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginNegative:

    def test_wrong_password_returns_401_or_400(self):
        """Incorrect password must be rejected with a 4xx status."""
        response = login(password="AbsolutelyWrongPassword999!")
        assert response.status_code in (400, 401), (
            f"Expected 400 or 401, got {response.status_code}"
        )

    def test_unregistered_email_returns_4xx(self):
        """An email that was never registered must fail with 4xx."""
        response = login(email=f"ghost_{uuid.uuid4().hex}@nowhere.invalid")
        assert response.status_code in (400, 401, 404), (
            f"Expected 4xx, got {response.status_code}"
        )

    def test_missing_email_field_returns_400(self):
        """Omitting email from the login body must return 400."""
        response = requests.post(
            f"{BASE}/auth/login",
            json={"password": "SomePassword123!"},
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_missing_password_field_returns_400(self):
        """Omitting password from the login body must return 400."""
        response = requests.post(
            f"{BASE}/auth/login",
            json={"email": os.getenv("TEST_EMAIL")},
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_empty_body_returns_400(self):
        """Sending an empty JSON object must return 400."""
        response = requests.post(f"{BASE}/auth/login", json={})
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_malformed_email_format_returns_400(self):
        """A string that is not a valid email address must be rejected."""
        response = requests.post(
            f"{BASE}/auth/login",
            json={"email": "not-an-email-at-all", "password": "Pass123!"},
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_failed_login_response_contains_error_message(self):
        """Failed login body must include a human-readable error field."""
        response = login(password="WrongPass!")
        assert response.status_code in (400, 401)
        body = response.json()
        has_error = (
            "message" in body
            or "error" in body
            or "detail" in body
            or "msg" in body
        )
        assert has_error, f"No error message in failed-login response: {body}"

    def test_password_reset_request_with_invalid_email_returns_4xx(self):
        """POST /auth/password-reset with bad email format must fail."""
        response = requests.post(
            f"{BASE}/auth/password-reset",
            json={"email": "not-valid"},
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginEdgeCases:

    def test_extra_unknown_fields_in_login_body_do_not_cause_500(self):
        """Unknown extra fields must be silently ignored, not crash the server."""
        response = requests.post(
            f"{BASE}/auth/login",
            json={
                "email": os.getenv("TEST_EMAIL"),
                "password": os.getenv("TEST_PASSWORD"),
                "role": "superadmin",
                "injected": "<script>alert(1)</script>",
            },
        )
        assert response.status_code != 500, (
            "Server must not 500 on unrecognised fields in the request body"
        )

    def test_extremely_long_password_does_not_cause_500(self):
        """A 10 000-character password must produce a 4xx, never a 500."""
        response = requests.post(
            f"{BASE}/auth/login",
            json={"email": "edge@example.com", "password": "X" * 10_000},
        )
        assert response.status_code in (400, 401, 422), (
            f"Expected 4xx, got {response.status_code}"
        )

    def test_onboard_status_requires_authentication(self, no_auth_headers):
        """GET /auth/onboard-status without a token must return 401."""
        response = requests.get(
            f"{BASE}/auth/onboard-status", headers=no_auth_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )
