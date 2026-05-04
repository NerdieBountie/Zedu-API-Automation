![CI Pipeline](https://github.com/NerdieBountie/Zedu-API-Automation/actions/workflows/ci.yml/badge.svg)
# Zedu API Automation Test Suite

Automated REST API test suite for the [Zedu](https://zedu.chat/) platform,
built with **Python + Pytest** against `https://api.zedu.chat`.

---

## Project Overview

This project provides structured, end-to-end API automation covering
authentication, user management, organisations, and channels. All tests are
**independent**, **idempotent**, and use **dynamically generated data** so
the full suite can be re-run any number of times without state conflicts.

---
## CI/CD Pipeline

This project uses **GitHub Actions** for Continuous Integration.

The pipeline triggers automatically on every push and pull request. It:
1. Sets up Python 3.11
2. Installs all dependencies from `requirements.txt`
3. Runs the full test suite with `pytest --junitxml=report.xml`
4. Uploads the JUnit XML report as a downloadable artifact
5. Fails the build if any test fails

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BASE_URL` | Base API URL e.g. `https://api.zedu.chat/api/v1` |
| `TEST_EMAIL` | Valid test account email |
| `TEST_PASSWORD` | Valid test account password |
| `EXPIRED_TOKEN` | An expired JWT token for negative auth tests |

These are stored as **GitHub Secrets** and injected automatically by the CI pipeline.
## Project Structure

```
zedu_api_tests/
│
├── tests/
│   ├── test_auth.py            # Authentication endpoint tests
│   ├── test_users.py           # User profile & preferences tests
│   ├── test_organisations.py   # Organisation CRUD tests
│   └── test_channels.py        # Channel CRUD tests
│
├── utils/
│   └── auth.py                 # Single login/token helper — shared by all tests
│
├── conftest.py                 # Shared pytest fixtures
├── .env.example                # Template — copy to .env and fill in values
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Test Coverage Summary

| File | Tests | Positive | Negative | Edge |
|---|---|---|---|---|
| `test_auth.py` | 16 | 5 | 8 | 3 |
| `test_users.py` | 14 | 5 | 6 | 3 |
| `test_organisations.py` | 14 | 5 | 6 | 3 |
| `test_channels.py` | 12 | 4 | 5 | 3 |
| **Total** | **56** | **19** | **25** | **12** |

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or higher |
| pip | bundled with Python ≥ 3.10 |

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-github-repo-url>
cd zedu_api_tests
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows PowerShell
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set real values:

```dotenv
BASE_URL=https://api.zedu.chat
TEST_EMAIL=your_registered_email@example.com
TEST_PASSWORD=YourRealPassword123!
EXPIRED_TOKEN=<paste an old expired JWT here>
```

> ⚠️ `.env` is listed in `.gitignore` and must **never** be committed.  
> The `.env` file is submitted separately to evaluators via the Google Doc link.

---

## How to Run the Test Suite

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_auth.py -v
pytest tests/test_users.py -v
pytest tests/test_organisations.py -v
pytest tests/test_channels.py -v
```

### Run a specific test by name keyword

```bash
pytest -k "test_valid_credentials" -v
```

### Generate an HTML report

```bash
pytest --html=reports/report.html --self-contained-html
```

---

## Test File Descriptions

### `tests/test_auth.py`
Covers `POST /auth/login`, `POST /auth/password-reset`, `GET /auth/onboard-status`.
- **Positive:** Valid login returns 200, response contains a token string, Content-Type is JSON.
- **Negative:** Wrong password, unregistered email, missing email field, missing password field, empty body, malformed email format, failed login returns error message, password-reset with invalid email.
- **Edge:** Extra unknown fields ignored, extremely long password produces 4xx not 500, onboard-status requires auth.

### `tests/test_users.py`
Covers `GET /users/me`, `GET /users/{userId}`, `GET /users/notification-preferences`.
- **Positive:** Authenticated /users/me returns 200 JSON with email string field.
- **Negative:** No token → 401, malformed token → 401, expired token → 401, nonexistent user ID → 404, invalid ID format → 4xx.
- **Edge:** GET /users/me is idempotent, token without Bearer prefix rejected, extra headers don't break the call.

### `tests/test_organisations.py`
Covers `POST /organisations`, `GET /organisations/{orgId}`, `GET /users/organisations`.
- **Positive:** Create org returns 201 with id field, fetch by ID returns 200 with name field, list user orgs returns 200.
- **Negative:** Create without auth → 401, empty body → 400, missing name → 400, nonexistent ID → 404, malformed token → 401, list without auth → 401.
- **Edge:** Special chars in name don't 500, very long name handled gracefully, 404 response is still valid JSON.

### `tests/test_channels.py`
Covers `POST /channels`, `GET /channels`, `GET /channels/{channelId}/`.
- **Positive:** List returns 200 JSON, create returns 200/201, fetch by ID returns 200.
- **Negative:** List without auth → 401, create without auth → 401, empty body → 400, nonexistent ID → 404, malformed token → 401.
- **Edge:** Duplicate channel name doesn't 500, special chars in name handled, Content-Type is always JSON.

---

## Design Principles

| Principle | Implementation |
|---|---|
| No hardcoded credentials/tokens | All values in `.env`, loaded via `python-dotenv` |
| Single login source | `utils/auth.py` is the only file that calls `/auth/login` |
| Dynamic test data | `uuid.uuid4()` + `Faker` generate unique values per run |
| Test independence | Every test sets up its own state; none depends on another |
| Idempotency | Re-running the suite never fails due to leftover data |
| Descriptive names | Test names state what is being tested and the expected outcome |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'dotenv'` | Run `pip install -r requirements.txt` |
| `ValueError: Login failed (401)` | Check `TEST_EMAIL` and `TEST_PASSWORD` in your `.env` |
| All tests fail with connection error | Verify `BASE_URL` in `.env` — no trailing slash |
| Channel/org tests skip | Those resources may require additional setup; check Swagger for required fields |
