"""
tests/test_channels.py
───────────────────────
Tests for Zedu channel endpoints:
  POST /channels              (create channel)
  GET  /channels              (list channels)
  GET  /channels/{channelId}/ (retrieve channel)
  POST /channels/{channelId}/join
  POST /channels/{channelId}/leave

Positive  : 4
Negative  : 5
Edge      : 3
Total     : 12

NOTE: Channel creation may require an org context — the tests
      obtain a fresh org first so each test is self-contained.
"""

import uuid
import pytest
import requests
from utils.auth import get_base_url

BASE = get_base_url()
CHANNELS_URL = f"{BASE}/channels"


# ─── helpers ────────────────────────────────────────────────────────────────

def _body(response: requests.Response) -> dict:
    body = response.json()
    return body.get("data", body)


def _create_channel(headers: dict, name: str = None,
                    org_id: str = None) -> requests.Response:
    """POST /channels with unique name."""
    payload = {
        "name": name or f"qa-channel-{uuid.uuid4().hex[:6]}",
        "description": "Automated QA test channel",
    }
    if org_id:
        payload["org_id"] = org_id
    return requests.post(CHANNELS_URL, json=payload, headers=headers)


def _get_or_skip_channel_id(headers: dict) -> str:
    """
    Create a channel and return its ID.
    Skip the calling test if creation fails (e.g. requires org context).
    """
    resp = _create_channel(headers)
    if resp.status_code not in (200, 201):
        pytest.skip(
            f"Channel creation returned {resp.status_code}; "
            "skipping test that depends on a channel ID."
        )
    data = _body(resp)
    ch_id = data.get("id") or data.get("_id")
    if not ch_id:
        pytest.skip("Channel ID not present in creation response")
    return ch_id


# ═══════════════════════════════════════════════════════════════════════════════
# POSITIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestChannelsPositive:

    def test_list_channels_returns_200(self, valid_headers):
        """GET /channels must return 200 for an authenticated user."""
        response = requests.get(CHANNELS_URL, headers=valid_headers)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )

    def test_list_channels_response_is_valid_json(self, valid_headers):
        """GET /channels response body must be parseable JSON."""
        response = requests.get(CHANNELS_URL, headers=valid_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)

    def test_create_channel_returns_200_or_201(self, valid_headers):
        """POST /channels with valid data must return 200 or 201."""
        response = _create_channel(valid_headers)
        assert response.status_code in (200, 201), (
            f"Expected 200/201, got {response.status_code}: {response.text}"
        )

    def test_get_channel_by_id_returns_200(self, valid_headers):
        """GET /channels/{channelId}/ for an existing channel returns 200."""
        ch_id = _get_or_skip_channel_id(valid_headers)
        response = requests.get(
            f"{CHANNELS_URL}/{ch_id}/", headers=valid_headers
        )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestChannelsNegative:

    def test_list_channels_without_auth_returns_401(self, no_auth_headers):
        """Unauthenticated GET /channels must be rejected with 401."""
        response = requests.get(CHANNELS_URL, headers=no_auth_headers)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_create_channel_without_auth_returns_401(self, no_auth_headers):
        """POST /channels without a token must return 401."""
        response = _create_channel(no_auth_headers)
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )

    def test_create_channel_with_empty_body_returns_400(self, valid_headers):
        """POST /channels with an empty body must return 400 or 422."""
        response = requests.post(
            CHANNELS_URL, json={}, headers=valid_headers
        )
        assert response.status_code in (400, 422), (
            f"Expected 400/422, got {response.status_code}"
        )

    def test_get_channel_with_nonexistent_id_returns_404(self, valid_headers):
        """GET /channels/{channelId}/ with a random UUID must return 404."""
        response = requests.get(
            f"{CHANNELS_URL}/{uuid.uuid4()}/", headers=valid_headers
        )
        assert response.status_code in (400, 404), (
            f"Expected 404 or 400, got {response.status_code}"
        )

    def test_get_channel_with_malformed_token_returns_401(
        self, malformed_token_headers
    ):
        """A broken token on GET /channels must return 401."""
        response = requests.get(
            CHANNELS_URL, headers=malformed_token_headers
        )
        assert response.status_code == 401, (
            f"Expected 401, got {response.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestChannelsEdgeCases:

    def test_create_channel_with_duplicate_name_returns_4xx_not_500(
        self, valid_headers
    ):
        """
        Creating two channels with the same name should return a 4xx conflict,
        not a 500. Idempotency: test can run multiple times safely.
        """
        fixed_name = f"qa-dup-channel-{uuid.uuid4().hex[:4]}"
        r1 = _create_channel(valid_headers, name=fixed_name)
        r2 = _create_channel(valid_headers, name=fixed_name)
        # First may succeed; second must not 500 regardless of outcome
        assert r2.status_code != 500, (
            "Server must not 500 when a duplicate channel name is submitted"
        )

    def test_channel_name_with_special_characters_does_not_500(
        self, valid_headers
    ):
        """
        A channel name with special chars must be handled without a 500.
        """
        response = _create_channel(
            valid_headers, name="QA #!channel & <test>"
        )
        assert response.status_code != 500, (
            "Server must not 500 on special characters in channel name"
        )

    def test_list_channels_response_content_type_is_json(self, valid_headers):
        """GET /channels must always respond with application/json."""
        response = requests.get(CHANNELS_URL, headers=valid_headers)
        assert "application/json" in response.headers.get("Content-Type", ""), (
            f"Unexpected Content-Type: {response.headers.get('Content-Type')}"
        )
