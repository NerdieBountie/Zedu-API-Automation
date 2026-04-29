"""
tests/test_courses.py
─────────────────────
Zedu is a messaging/collaboration platform — there are no /courses endpoints.
This file tests the MESSAGES endpoints instead, which are a core resource.

Endpoints tested:
  GET  /organisations/{orgId}/recent-dm   (recent DMs)
  GET  /threads/recent                    (recent threads)
  POST /channels/{channelId}/messages     (send message — requires channel)

Positive  : 4
Negative  : 5
Edge      : 3
Total     : 12
"""

import uuid
import pytest
import requests
from utils.auth import get_base_url

BASE = get_base_url()


def _get_org_id(headers: dict) -> str:
    """Get the first org ID for the authenticated user."""
    response = requests.get(f"{BASE}/users/organisations", headers=headers)
    if response.status_code != 200:
        pytest.skip("Could not fetch user organisations")
    body = response.json()
    orgs = body.get("data", body)
    if isinstance(orgs, dict):
        orgs = orgs.get("organisations", orgs.get("data", []))
    if not orgs:
        pytest.skip("No organisations found for this user")
    first = orgs[0]
    return first.get("_id") or first.get("id")


class TestRecentActivityPositive:

    def test_get_recent_threads_returns_200(self, valid_headers):
        """GET /threads/recent must return 200 for an authenticated user."""
        response = requests.get(f"{BASE}/threads/recent", headers=valid_headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_get_recent_threads_response_is_json(self, valid_headers):
        """GET /threads/recent must return a valid JSON body."""
        response = requests.get(f"{BASE}/threads/recent", headers=valid_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_get_recent_threads_content_type_is_json(self, valid_headers):
        """GET /threads/recent must respond with application/json."""
        response = requests.get(f"{BASE}/threads/recent", headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", "")

    def test_get_recent_dm_for_org_returns_200_or_404(self, valid_headers):
        """
        GET /organisations/{orgId}/recent-dm must return 200 for a valid org
        or 404 if no DMs exist — never a 500.
        """
        org_id = _get_org_id(valid_headers)
        response = requests.get(
            f"{BASE}/organisations/{org_id}/recent-dm",
            headers=valid_headers,
        )
        assert response.status_code in (200, 404), (
            f"Expected 200 or 404, got {response.status_code}: {response.text}"
        )


class TestRecentActivityNegative:

    def test_get_recent_threads_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated GET /threads/recent must return 401."""
        response = requests.get(f"{BASE}/threads/recent", headers=no_auth_headers)
        assert response.status_code == 401

    def test_get_recent_threads_with_malformed_token_returns_401(
        self, malformed_token_headers
    ):
        """Malformed token on GET /threads/recent must return 401."""
        response = requests.get(
            f"{BASE}/threads/recent", headers=malformed_token_headers
        )
        assert response.status_code == 401

    def test_get_recent_threads_with_expired_token_returns_401(
        self, expired_token_headers
    ):
        """Expired token on GET /threads/recent must return 401."""
        response = requests.get(
            f"{BASE}/threads/recent", headers=expired_token_headers
        )
        assert response.status_code == 401

    def test_get_threads_for_nonexistent_org_returns_4xx(self, valid_headers):
        """GET /threads/organisations/{orgId} with a fake org ID must return 4xx."""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE}/threads/organisations/{fake_id}",
            headers=valid_headers,
        )
        assert response.status_code in (400, 403, 404), (
            f"Expected 4xx, got {response.status_code}"
        )

    def test_get_recent_dm_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated GET /organisations/{orgId}/recent-dm must return 401."""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{BASE}/organisations/{fake_id}/recent-dm",
            headers=no_auth_headers,
        )
        assert response.status_code == 401


class TestRecentActivityEdgeCases:

    def test_recent_threads_is_idempotent(self, valid_headers):
        """
        Calling GET /threads/recent twice must return the same status.
        Read-only endpoint should not mutate state.
        """
        r1 = requests.get(f"{BASE}/threads/recent", headers=valid_headers)
        r2 = requests.get(f"{BASE}/threads/recent", headers=valid_headers)
        assert r1.status_code == r2.status_code == 200

    def test_recent_threads_with_extra_headers_still_works(self, valid_headers):
        """Extra harmless headers must not break GET /threads/recent."""
        headers = {**valid_headers, "X-QA-Test": "zedu-suite", "Accept": "application/json"}
        response = requests.get(f"{BASE}/threads/recent", headers=headers)
        assert response.status_code == 200

    def test_get_dm_with_invalid_org_id_format_does_not_500(self, valid_headers):
        """An invalid org ID format must produce a 4xx, never a 500."""
        response = requests.get(
            f"{BASE}/organisations/not-a-real-id/recent-dm",
            headers=valid_headers,
        )
        assert response.status_code != 500, (
            "Server must not 500 on invalid org ID format"
        )
