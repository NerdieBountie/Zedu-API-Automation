"""
tests/test_organisations.py
────────────────────────────
Tests for Zedu organisation endpoints:
  POST /organisations          (create)
  GET  /organisations/{orgId}  (retrieve)
  PUT  /organisations/{orgId}  (update)
  GET  /users/organisations    (list current user's orgs)

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
ORGS_URL = f"{BASE}/organisations"


# ─── helpers ────────────────────────────────────────────────────────────────

def _body(response: requests.Response) -> dict:
    body = response.json()
    return body.get("data", body)


def _create_org(headers: dict, name: str = None) -> requests.Response:
    """POST /organisations with a unique name."""
    return requests.post(
        ORGS_URL,
        json={
            "name": name or f"QA Org {uuid.uuid4().hex[:6]}",
            "description": "Automated test organisation",
        },
        headers=headers,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrganisationsPositive:

    def test_create_organisation_returns_200_or_201(self, valid_headers):
        """POST /organisations with valid data must succeed."""
        response = _create_org(valid_headers)
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}: {response.text}"
        )

    def test_created_organisation_response_contains_id(self, valid_headers):
        """Create-org response body must include an id field."""
        response = _create_org(valid_headers)
        assert response.status_code in (200, 201)
        data = _body(response)
        org_id = data.get("id") or data.get("_id")
        assert org_id is not None, f"No 'id' in response: {data}"

    def test_get_organisation_by_id_returns_200(self, valid_headers):
        """GET /organisations/{orgId} for a just-created org must return 200."""
        create_resp = _create_org(valid_headers)
        assert create_resp.status_code in (200, 201)
        org_id = (_body(create_resp).get("id")
                  or _body(create_resp).get("_id"))
        if not org_id:
            pytest.skip("Could not obtain org ID from creation response")

        response = requests.get(
            f"{ORGS_URL}/{org_id}", headers=valid_headers
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_get_organisation_response_contains_name_field(
        self, valid_headers
    ):
        """Retrieved organisation must contain a 'name' field."""
        create_resp = _create_org(valid_headers)
        assert create_resp.status_code in (200, 201)
        org_id = (_body(create_resp).get("id")
                  or _body(create_resp).get("_id"))
        if not org_id:
            pytest.skip("Could not obtain org ID")
        get_resp = requests.get(f"{ORGS_URL}/{org_id}", headers=valid_headers)
        assert get_resp.status_code == 200
        data = _body(get_resp)
        assert "name" in data, f"'name' field missing in: {data}"

    def test_list_user_organisations_returns_200(self, valid_headers):
        """GET /users/organisations must return 200 for an authenticated user."""
        response = requests.get(
            f"{BASE}/users/organisations", headers=valid_headers
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrganisationsNegative:

    def test_create_org_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated POST /organisations must return 401."""
        response = _create_org(no_auth_headers)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_create_org_with_empty_body_returns_400(self, valid_headers):
        """POST /organisations with an empty body must return 400 or 422."""
        response = requests.post(ORGS_URL, json={}, headers=valid_headers)
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_create_org_missing_name_returns_400(self, valid_headers):
        """POST /organisations without the required 'name' field must fail."""
        response = requests.post(
            ORGS_URL,
            json={"description": "No name provided"},
            headers=valid_headers,
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_get_org_with_nonexistent_id_returns_404(self, valid_headers):
        """GET /organisations/{orgId} with a random UUID must return 404."""
        response = requests.get(
            f"{ORGS_URL}/{uuid.uuid4()}", headers=valid_headers
        )
        assert response.status_code in (400, 404), (
            f"Expected 404 or 400, got {response.status_code}"
        )

    def test_get_org_with_malformed_token_returns_401(
        self, malformed_token_headers
    ):
        """Malformed token on GET /organisations/{orgId} must return 401."""
        response = requests.get(
            f"{ORGS_URL}/{uuid.uuid4()}", headers=malformed_token_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_list_user_orgs_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated GET /users/organisations must return 401."""
        response = requests.get(
            f"{BASE}/users/organisations", headers=no_auth_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestOrganisationsEdgeCases:

    def test_create_org_name_with_special_characters_does_not_500(
        self, valid_headers
    ):
        """
        An org name containing special characters must not cause a server error.
        The API may accept or reject it, but must not crash.
        """
        response = _create_org(
            valid_headers, name="QA <Org> 'Test' & \"Suite\" 2025"
        )
        assert response.status_code != 500, (
            "Server must not 500 on special characters in org name"
        )

    def test_create_org_with_very_long_name_returns_4xx_or_success(
        self, valid_headers
    ):
        """
        An extremely long org name (1000 chars) must produce a 4xx or succeed
        gracefully — never a 500.
        """
        response = _create_org(valid_headers, name="A" * 1000)
        assert response.status_code != 500, (
            f"Server must not 500 on very long org name: {response.status_code}"
        )

    def test_get_org_response_is_json(self, valid_headers):
        """
        Even for a 404 (nonexistent org), the response body must be valid JSON.
        """
        response = requests.get(
            f"{ORGS_URL}/{uuid.uuid4()}", headers=valid_headers
        )
        assert response.status_code in (400, 404)
        try:
            body = response.json()
            assert isinstance(body, dict)
        except Exception as exc:
            pytest.fail(f"Response body is not valid JSON: {exc}")
