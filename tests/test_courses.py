"""
tests/test_courses.py

Test suite for Zedu API course / content endpoints.

Zedu is an educational chat platform; courses or learning content are the
core resource type. Adjust the endpoint paths (e.g. /courses, /content,
/lessons) to match what the Swagger docs expose.

Covers:
  - GET  /courses          (list courses)
  - GET  /courses/{id}     (fetch single course)
  - POST /courses          (create course — if permitted by role)

Positive cases : 4
Negative cases : 5  (cumulative total with auth/user tests now ≥ 10)
Edge cases      : 3
Total           : 12
"""

import uuid
import pytest
import requests
from utils.auth import get_base_url

BASE = get_base_url()

# Adjust these to match the actual Swagger endpoint paths
COURSES_ENDPOINT = f"{BASE}/courses"


# ===========================================================================
# Positive Tests
# ===========================================================================

class TestListCoursesPositive:

    def test_list_courses_returns_200_when_authenticated(self, valid_headers):
        """Authenticated GET /courses must return HTTP 200."""
        response = requests.get(COURSES_ENDPOINT, headers=valid_headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_list_courses_response_is_json(self, valid_headers):
        """GET /courses must return a JSON body."""
        response = requests.get(COURSES_ENDPOINT, headers=valid_headers)
        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", ""), (
            "Expected JSON Content-Type"
        )
        # Must be parseable
        data = response.json()
        assert data is not None

    def test_list_courses_response_is_list_or_object(self, valid_headers):
        """Course list response body must be a list or dict (not a scalar)."""
        response = requests.get(COURSES_ENDPOINT, headers=valid_headers)
        assert response.status_code == 200
        data = response.json()
        body = data.get("data", data)
        assert isinstance(body, (list, dict)), (
            f"Expected list or dict, got {type(body)}"
        )

    def test_get_single_course_returns_200_for_valid_id(self, valid_headers):
        """
        Fetch the list first, pick the first ID, then verify GET /courses/{id}.
        Skips if no courses exist yet.
        """
        list_response = requests.get(COURSES_ENDPOINT, headers=valid_headers)
        if list_response.status_code != 200:
            pytest.skip("Cannot list courses — skipping single-course test")
        data = list_response.json()
        items = data.get("data", data)
        if isinstance(items, dict):
            items = items.get("items", items.get("results", []))
        if not items:
            pytest.skip("No courses available to test individual fetch")
        first_id = items[0].get("id") or items[0].get("_id")
        response = requests.get(
            f"{COURSES_ENDPOINT}/{first_id}", headers=valid_headers
        )
        assert response.status_code == 200, (
            f"Expected 200 for course {first_id}, got {response.status_code}"
        )


# ===========================================================================
# Negative Tests
# ===========================================================================

class TestCoursesNegative:

    def test_list_courses_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated GET /courses must be rejected with 401."""
        response = requests.get(COURSES_ENDPOINT, headers=no_auth_headers)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_get_course_by_nonexistent_id_returns_404(self, valid_headers):
        """Random UUID that maps to no course must produce 404."""
        fake_id = str(uuid.uuid4())
        response = requests.get(
            f"{COURSES_ENDPOINT}/{fake_id}", headers=valid_headers
        )
        assert response.status_code in (404, 400), (
            f"Expected 404 or 400, got {response.status_code}"
        )

    def test_get_course_with_malformed_token_returns_401(
        self, malformed_token_headers
    ):
        """Malformed token must not grant access to courses."""
        response = requests.get(
            COURSES_ENDPOINT, headers=malformed_token_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_create_course_with_missing_required_fields_returns_400(
        self, valid_headers
    ):
        """POST /courses with an empty body should return 400 or 422."""
        response = requests.post(COURSES_ENDPOINT, json={}, headers=valid_headers)
        assert response.status_code in (400, 422, 403), (
            f"Expected 400/422/403, got {response.status_code}"
        )

    def test_create_course_with_invalid_data_types_returns_400(
        self, valid_headers
    ):
        """Numeric field sent as string should be rejected with 400/422."""
        payload = {
            "title": 12345,          # should be string
            "duration": "not-a-number",  # should be int/float
        }
        response = requests.post(
            COURSES_ENDPOINT, json=payload, headers=valid_headers
        )
        assert response.status_code in (400, 422, 403), (
            f"Expected 400/422/403, got {response.status_code}"
        )


# ===========================================================================
# Edge Cases
# ===========================================================================

class TestCoursesEdgeCases:

    def test_list_courses_with_large_page_number_returns_empty_or_200(
        self, valid_headers
    ):
        """
        Requesting a very high page number should return empty results
        or 200, never a 500.
        """
        response = requests.get(
            COURSES_ENDPOINT,
            params={"page": 999999, "limit": 10},
            headers=valid_headers,
        )
        assert response.status_code in (200, 400, 404), (
            f"Server must not crash on high page number: {response.status_code}"
        )

    def test_list_courses_with_zero_limit_handled_gracefully(
        self, valid_headers
    ):
        """limit=0 is an out-of-range value; must not cause a 500."""
        response = requests.get(
            COURSES_ENDPOINT,
            params={"limit": 0},
            headers=valid_headers,
        )
        assert response.status_code != 500, (
            "Server must not return 500 for limit=0"
        )

    def test_list_courses_with_negative_page_handled_gracefully(
        self, valid_headers
    ):
        """Negative page number is invalid input; must not cause a 500."""
        response = requests.get(
            COURSES_ENDPOINT,
            params={"page": -1},
            headers=valid_headers,
        )
        assert response.status_code != 500, (
            "Server must not return 500 for page=-1"
        )
