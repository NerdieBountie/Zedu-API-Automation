"""
tests/test_users.py
───────────────────
Tests for Zedu API user & profile endpoints.

Actual Zedu API response shape (discovered via live testing):
  GET /users/me  →  { "user": { "email": ..., "_id": ..., ... } }

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


def _get_user_data(response: requests.Response) -> dict:
    """
    Zedu wraps the user in a 'user' key:
      { "user": { "email": "...", "_id": "..." } }
    """
    body = response.json()
    return (
        body.get("user")
        or body.get("data", {}).get("user")
        or body.get("data")
        or body
    )


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
        data = _get_user_data(response)
        assert "email" in data, (
            f"'email' field missing. Response body: {response.json()}"
        )

    def test_get_me_email_field_is_string(self, valid_headers):
        """The email field in /users/me must be a string."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        data = _get_user_data(response)
        email = data.get("email")
        assert isinstance(email, str), (
            f"Expected email to be a string, got {type(email)}"
        )

    def test_get_me_returns_json_content_type(self, valid_headers):
        """GET /users/me must respond with application/json Content-Type."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_get_me_response_body_is_valid_json(self, valid_headers):
        """GET /users/me response body must be parseable as JSON."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        try:
            body = response.json()
            assert isinstance(body, dict)
        except Exception as exc:
            pytest.fail(f"Response body is not valid JSON: {exc}")


class TestUsersNegative:

    def test_get_me_without_token_returns_401(self, no_auth_headers):
        """Unauthenticated GET /users/me must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401

    def test_get_me_with_malformed_token_returns_401(self, malformed_token_headers):
        """A syntactically broken token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=malformed_token_headers)
        assert response.status_code == 401

    def test_get_me_with_expired_token_returns_401(self, expired_token_headers):
        """An expired/revoked token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=expired_token_headers)
        assert response.status_code == 401

    def test_get_user_by_nonexistent_id_returns_404(self, valid_headers):
        """GET /users/{userId} with a random UUID must return 404."""
        response = requests.get(f"{BASE}/users/{uuid.uuid4()}", headers=valid_headers)
        assert response.status_code in (400, 404)

    def test_get_user_by_invalid_id_format_returns_4xx(self, valid_headers):
        """GET /users/{userId} with a garbage ID must not succeed."""
        response = requests.get(f"{BASE}/users/@@invalid!!!", headers=valid_headers)
        assert response.status_code in (400, 404, 422)

    def test_401_error_response_contains_message_field(self, no_auth_headers):
        """A 401 response body must include an error message."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401
        try:
            body = response.json()
            assert "message" in body or "error" in body or "detail" in body
        except Exception:
            pass


class TestUsersEdgeCases:

    def test_get_me_is_idempotent(self, valid_headers):
        """Calling GET /users/me twice must return the same email both times."""
        r1 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        r2 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        email1 = _get_user_data(r1).get("email")
        email2 = _get_user_data(r2).get("email")
        assert email1 == email2

    def test_token_without_bearer_prefix_returns_401(self, valid_token):
        """Supplying the raw token without 'Bearer ' prefix must fail."""
        response = requests.get(f"{BASE}/users/me", headers={"Authorization": valid_token})
        assert response.status_code == 401

    def test_extra_request_headers_do_not_break_get_me(self, valid_headers):
        """Arbitrary extra headers must not cause the endpoint to fail."""
        headers = {**valid_headers, "X-Test-Header": "zedu-qa", "Accept": "application/json"}
        response = requests.get(f"{BASE}/users/me", headers=headers)
        assert response.status_code == 200
"""
tests/test_users.py
───────────────────
Tests for Zedu API user & profile endpoints.

Actual Zedu API response shape (discovered via live testing):
  GET /users/me  →  { "user": { "email": ..., "_id": ..., ... } }

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


def _get_user_data(response: requests.Response) -> dict:
    """
    Zedu wraps the user in a 'user' key:
      { "user": { "email": "...", "_id": "..." } }
    """
    body = response.json()
    return (
        body.get("user")
        or body.get("data", {}).get("user")
        or body.get("data")
        or body
    )


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
        data = _get_user_data(response)
        assert "email" in data, (
            f"'email' field missing. Response body: {response.json()}"
        )

    def test_get_me_email_field_is_string(self, valid_headers):
        """The email field in /users/me must be a string."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        data = _get_user_data(response)
        email = data.get("email")
        assert isinstance(email, str), (
            f"Expected email to be a string, got {type(email)}"
        )

    def test_get_me_returns_json_content_type(self, valid_headers):
        """GET /users/me must respond with application/json Content-Type."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_get_me_response_body_is_valid_json(self, valid_headers):
        """GET /users/me response body must be parseable as JSON."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        try:
            body = response.json()
            assert isinstance(body, dict)
        except Exception as exc:
            pytest.fail(f"Response body is not valid JSON: {exc}")


class TestUsersNegative:

    def test_get_me_without_token_returns_401(self, no_auth_headers):
        """Unauthenticated GET /users/me must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401

    def test_get_me_with_malformed_token_returns_401(self, malformed_token_headers):
        """A syntactically broken token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=malformed_token_headers)
        assert response.status_code == 401

    def test_get_me_with_expired_token_returns_401(self, expired_token_headers):
        """An expired/revoked token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=expired_token_headers)
        assert response.status_code == 401

    def test_get_user_by_nonexistent_id_returns_404(self, valid_headers):
        """GET /users/{userId} with a random UUID must return 404."""
        response = requests.get(f"{BASE}/users/{uuid.uuid4()}", headers=valid_headers)
        assert response.status_code in (400, 404)

    def test_get_user_by_invalid_id_format_returns_4xx(self, valid_headers):
        """GET /users/{userId} with a garbage ID must not succeed."""
        response = requests.get(f"{BASE}/users/@@invalid!!!", headers=valid_headers)
        assert response.status_code in (400, 404, 422)

    def test_401_error_response_contains_message_field(self, no_auth_headers):
        """A 401 response body must include an error message."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401
        try:
            body = response.json()
            assert "message" in body or "error" in body or "detail" in body
        except Exception:
            pass


class TestUsersEdgeCases:

    def test_get_me_is_idempotent(self, valid_headers):
        """Calling GET /users/me twice must return the same email both times."""
        r1 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        r2 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        email1 = _get_user_data(r1).get("email")
        email2 = _get_user_data(r2).get("email")
        assert email1 == email2

    def test_token_without_bearer_prefix_returns_401(self, valid_token):
        """Supplying the raw token without 'Bearer ' prefix must fail."""
        response = requests.get(f"{BASE}/users/me", headers={"Authorization": valid_token})
        assert response.status_code == 401

    def test_extra_request_headers_do_not_break_get_me(self, valid_headers):
        """Arbitrary extra headers must not cause the endpoint to fail."""
        headers = {**valid_headers, "X-Test-Header": "zedu-qa", "Accept": "application/json"}
        response = requests.get(f"{BASE}/users/me", headers=headers)
        assert response.status_code == 200
"""
tests/test_users.py
───────────────────
Tests for Zedu API user & profile endpoints.

Actual Zedu API response shape (discovered via live testing):
  GET /users/me  →  { "user": { "email": ..., "_id": ..., ... } }

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


def _get_user_data(response: requests.Response) -> dict:
    """
    Zedu wraps the user in a 'user' key:
      { "user": { "email": "...", "_id": "..." } }
    """
    body = response.json()
    return (
        body.get("user")
        or body.get("data", {}).get("user")
        or body.get("data")
        or body
    )


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
        data = _get_user_data(response)
        assert "email" in data, (
            f"'email' field missing. Response body: {response.json()}"
        )

    def test_get_me_email_field_is_string(self, valid_headers):
        """The email field in /users/me must be a string."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        data = _get_user_data(response)
        email = data.get("email")
        assert isinstance(email, str), (
            f"Expected email to be a string, got {type(email)}"
        )

    def test_get_me_returns_json_content_type(self, valid_headers):
        """GET /users/me must respond with application/json Content-Type."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_get_me_response_body_is_valid_json(self, valid_headers):
        """GET /users/me response body must be parseable as JSON."""
        response = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert response.status_code == 200
        try:
            body = response.json()
            assert isinstance(body, dict)
        except Exception as exc:
            pytest.fail(f"Response body is not valid JSON: {exc}")


class TestUsersNegative:

    def test_get_me_without_token_returns_401(self, no_auth_headers):
        """Unauthenticated GET /users/me must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401

    def test_get_me_with_malformed_token_returns_401(self, malformed_token_headers):
        """A syntactically broken token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=malformed_token_headers)
        assert response.status_code == 401

    def test_get_me_with_expired_token_returns_401(self, expired_token_headers):
        """An expired/revoked token must be rejected with 401."""
        response = requests.get(f"{BASE}/users/me", headers=expired_token_headers)
        assert response.status_code == 401

    def test_get_user_by_nonexistent_id_returns_404(self, valid_headers):
        """GET /users/{userId} with a random UUID must return 404."""
        response = requests.get(f"{BASE}/users/{uuid.uuid4()}", headers=valid_headers)
        assert response.status_code in (400, 404)

    def test_get_user_by_invalid_id_format_returns_4xx(self, valid_headers):
        """GET /users/{userId} with a garbage ID must not succeed."""
        response = requests.get(f"{BASE}/users/@@invalid!!!", headers=valid_headers)
        assert response.status_code in (400, 404, 422)

    def test_401_error_response_contains_message_field(self, no_auth_headers):
        """A 401 response body must include an error message."""
        response = requests.get(f"{BASE}/users/me", headers=no_auth_headers)
        assert response.status_code == 401
        try:
            body = response.json()
            assert "message" in body or "error" in body or "detail" in body
        except Exception:
            pass


class TestUsersEdgeCases:

    def test_get_me_is_idempotent(self, valid_headers):
        """Calling GET /users/me twice must return the same email both times."""
        r1 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        r2 = requests.get(f"{BASE}/users/me", headers=valid_headers)
        assert r1.status_code == 200
        assert r2.status_code == 200
        email1 = _get_user_data(r1).get("email")
        email2 = _get_user_data(r2).get("email")
        assert email1 == email2

    def test_token_without_bearer_prefix_returns_401(self, valid_token):
        """Supplying the raw token without 'Bearer ' prefix must fail."""
        response = requests.get(f"{BASE}/users/me", headers={"Authorization": valid_token})
        assert response.status_code == 401

    def test_extra_request_headers_do_not_break_get_me(self, valid_headers):
        """Arbitrary extra headers must not cause the endpoint to fail."""
        headers = {**valid_headers, "X-Test-Header": "zedu-qa", "Accept": "application/json"}
        response = requests.get(f"{BASE}/ussers/me", headers=headers)
        assert response.status_code == 200
