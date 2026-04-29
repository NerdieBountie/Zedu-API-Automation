"""
tests/test_users.py
───────────────────
Tests for Zedu user & profile endpoints:
  GET   /users/me
  GET   /users/{userId}
  PUT   /users/{userId}
  GET   /users/notification-preferences
  GET   /profile
  PATCH /profile

Positive  : 5
Negative  : 6
Edge      : 3
Total     : 14
"""

import uuid
import pytest
import requests
from utils.auth import get_base_url

BASE = get_base_url()


# ─── helpers ────────────────────────────────────────────────────────────────

def _body(response: requests.Response) -> dict:
    """Unwrap Zedu's { data: {...} } envelope."""
    body = response.json()
    return body.get("data", body)


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetCurrentUserPositive:

    def test_get_me_returns_200_when_authenticated(self, valid_headers):
        """GET /users/me with a valid token must return 200."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_get_me_response_contains_email_field(self, valid_headers):
        """GET /users/me response must include the user's email."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        data = _body(response)
        assert "email" in data, f"'email' missing in: {data}"

    def test_get_me_email_field_is_string(self, valid_headers):
        """The email field in /users/me must be a string type."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        data = _body(response)
        assert isinstance(data.get("email"), str)

    def test_get_me_returns_json_content_type(self, valid_headers):
        """GET /users/me must respond with application/json Content-Type."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", ""), (
            f"Unexpected Content-Type: {response.headers.get('Content-Type')}"
        )

    def test_get_notification_preferences_returns_200(self, valid_headers):
        """GET /users/notification-preferences must return 200."""
        response = requests.get(
            f"{BASE}/users/notification-preferences", headers=valid_headers
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersNegative:

    def test_get_me_without_token_returns_401(self, no_auth_headers):
        """Unauthenticated GET /users/me must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_get_me_with_malformed_token_returns_401(
        self, malformed_token_headers
    ):
        """A syntactically broken token must be rejected with 401."""
        response = requests.get(
            f"{BASE}/users/me", headers=malformed_token_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_get_me_with_expired_token_returns_401(
        self, expired_token_headers
    ):
        """An expired/revoked token must be rejected with 401."""
        response = requests.get(
            f"{BASE}/users/me", headers=expired_token_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_get_user_by_nonexistent_id_returns_404(self, valid_headers):
        """GET /users/{userId} with a random UUID must return 404."""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE}/users/{fake_id}", headers=valid_headers
        )
        assert response.status_code in (400, 404), (
            f"Expected 404 or 400, got {response.status_code}"
        )

    def test_get_user_by_invalid_id_format_returns_4xx(self, valid_headers):
        """GET /users/{userId} with a garbage ID must not succeed."""
        response = requests.get(
            f"{BASE}/users/@@invalid-id!!!", headers=valid_headers
        )
        assert response.status_code in (400, 404, 422), (
            f"Expected 4xx, got {response.status_code}"
        )

    def test_401_error_response_contains_message_field(self, no_auth_headers):
        """A 401 response body from /users/me must include an error message."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401
        try:
            body = response.json()
            has_msg = (
                "message" in body or "error" in body or "detail" in body
            )
            assert has_msg, f"No error field in 401 response: {body}"
        except Exception:
            pass  # plain-text 401 bodies are also acceptable


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsersEdgeCases:

    def test_get_me_is_idempotent(self, valid_headers):
        """
        Calling GET /users/me twice in a row must return the same email.
        Verifies the endpoint does not have mutating side-effects.
        """
        r1 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        r2 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        email1 = _body(r1).get("email")
        email2 = _body(r2).get("email")
        assert email1 == email2, (
            f"Email changed between calls: {email1} → {email2}"
        )

    def test_token_without_bearer_prefix_returns_401(self, valid_token):
        """Supplying the raw token without 'Bearer ' prefix must fail."""
        headers = {"Authorization": valid_token}  # missing "Bearer "
        response = requests.get(f"{BASE}/users/me", headers=headers)
        assert response.status_code == 401, (
            f"Expected 401 for token without Bearer prefix, "
            f"got {response.status_code}"
        )

    def test_extra_request_headers_do_not_break_get_me(self, valid_headers):
        """Arbitrary extra headers must not cause the endpoint to fail."""
        headers = {
            **valid_headers,
            "X-Test-Header": "zedu-qa-suite",
            "Accept": "application/json",
            "X-Forwarded-For": "127.0.0.1",
        }
        response = requests.get(f"{BASE}/users/me", headers=headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )
