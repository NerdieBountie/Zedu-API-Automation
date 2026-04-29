import uuid
import pytest
import requests
from utils.auth import get_base_url

BASE = get_base_url()
ORGS_URL = f"{BASE}/organisations"


def _body(r):
    b = r.json()
    return b.get("data", b)


def _create_org(headers, name=None):
    return requests.post(
        ORGS_URL,
        json={
            "name": name or f"QA Org {uuid.uuid4().hex[:6]}",
            "description": "QA test org",
            "country": "Nigeria",
            "type": "workspace",
        },
        headers=headers,
    )


class TestOrganisationsPositive:
    def test_create_organisation_returns_200_or_201(self, valid_headers):
        """POST /organisations with valid data must succeed."""
        r = _create_org(valid_headers)
        assert r.status_code in (200, 201), f"Got {r.status_code}: {r.text}"

    def test_created_organisation_response_contains_id(self, valid_headers):
        """Create-org response must include an id field."""
        r = _create_org(valid_headers)
        assert r.status_code in (200, 201)
        d = _body(r)
        assert d.get("id") or d.get("_id"), f"No id in: {d}"

    def test_get_organisation_by_id_returns_200(self, valid_headers):
        """GET /organisations/{orgId} for a created org must return 200."""
        r = _create_org(valid_headers)
        assert r.status_code in (200, 201)
        d = _body(r)
        oid = d.get("id") or d.get("_id")
        if not oid:
            pytest.skip("No org ID")
        r2 = requests.get(f"{ORGS_URL}/{oid}", headers=valid_headers)
        assert r2.status_code == 200, f"Got {r2.status_code}: {r2.text}"

    def test_get_organisation_response_contains_name_field(self, valid_headers):
        """Retrieved organisation must contain a name field."""
        r = _create_org(valid_headers)
        assert r.status_code in (200, 201)
        d = _body(r)
        oid = d.get("id") or d.get("_id")
        if not oid:
            pytest.skip("No org ID")
        r2 = requests.get(f"{ORGS_URL}/{oid}", headers=valid_headers)
        assert r2.status_code == 200
        assert "name" in _body(r2)

    def test_list_user_organisations_returns_200(self, valid_headers):
        """GET /users/organisations must return 200."""
        r = requests.get(f"{BASE}/users/organisations", headers=valid_headers)
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"


class TestOrganisationsNegative:
    def test_create_org_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated POST /organisations must return 401."""
        assert _create_org(no_auth_headers).status_code == 401

    def test_create_org_with_empty_body_returns_400(self, valid_headers):
        """Empty body must return 400 or 422."""
        r = requests.post(ORGS_URL, json={}, headers=valid_headers)
        assert r.status_code in (400, 422)

    def test_create_org_missing_name_returns_400(self, valid_headers):
        """Missing name field must return 400 or 422."""
        r = requests.post(
            ORGS_URL,
            json={"description": "no name", "country": "Nigeria", "type": "workspace"},
            headers=valid_headers,
        )
        assert r.status_code in (400, 422)

    def test_get_org_with_nonexistent_id_returns_404(self, valid_headers):
        """Random UUID must return 404."""
        r = requests.get(f"{ORGS_URL}/{uuid.uuid4()}", headers=valid_headers)
        assert r.status_code in (400, 404)

    def test_get_org_with_malformed_token_returns_401(self, malformed_token_headers):
        """Malformed token must return 401."""
        r = requests.get(f"{ORGS_URL}/{uuid.uuid4()}", headers=malformed_token_headers)
        assert r.status_code == 401

    def test_list_user_orgs_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated list orgs must return 401."""
        r = requests.get(f"{BASE}/users/organisations", headers=no_auth_headers)
        assert r.status_code == 401

class TestOrganisationsEdgeCases:
    def test_create_org_special_characters_does_not_500(self, valid_headers):
        """Special chars in name must not cause 500."""
        r = _create_org(valid_headers, name="QA <Org> & Test 2025")
        assert r.status_code != 500

    def test_create_org_very_long_name_does_not_500(self, valid_headers):
        """500-char name must not cause 500."""
        r = _create_org(valid_headers, name="A" * 500)
        assert r.status_code != 500

    def test_get_org_error_response_is_valid_json(self, valid_headers):
        """404 response must be valid JSON."""
        r = requests.get(f"{ORGS_URL}/{uuid.uuid4()}", headers=valid_headers)
        assert r.status_code in (400, 404)
        assert isinstance(r.json(), dict)