# Mini SIP Tracker Backend

This project implements a backend for a Systematic Investment Plan (SIP) tracker, built with FastAPI, using Supabase JWT for authentication and PostgreSQL (Supabase's underlying database) for data storage. It includes core features, unit tests, and a Dockerized setup, alongside a detailed system design document.

## Table of Contents

1.  [Features](#1-features)
2.  [Tech Stack](#2-tech-stack)
3.  [Getting Started](#3-getting-started)
    * [Prerequisites](#prerequisites)
    * [Local Setup](#local-setup)
    * [Supabase JWT Setup](#supabase-jwt-setup)
    * [Running with Docker Compose](#running-with-docker-compose)
4.  [API Usage](#4-api-usage)
    * [Authentication](#authentication)
    * [Create SIP Plan (`POST /sips/`)](#create-sip-plan-post-sips)
    * [Get SIP Summary (`GET /sips/summary`)](#get-sip-summary-get-sips-summary)
5.  [Running Tests](#5-running-tests)
6.  [System Design Document](#6-system-design-document)
7.  [Assignment Completion Notes](#7-assignment-completion-notes)

## 1. Features

* **User Authentication**: Secure user authentication using Supabase JWT.
* **Create SIP Plan**: API endpoint to allow authenticated users to create and store monthly SIP plans.
* **Get SIP Summary**: API endpoint to retrieve a summary of all SIPs for an authenticated user, grouped by scheme, with calculated total invested amount and months invested.
* **Database**: Supabase PostgreSQL as the primary data store.
* **ORM**: SQLAlchemy for database interactions.
* **Containerization**: Docker and Docker Compose setup for easy deployment.
* **Unit Tests**: Basic `pytest` suite for core API functionalities.

## 2. Tech Stack

* **Backend Framework**: FastAPI
* **Authentication**: Supabase JWT
* **Database**: Supabase PostgreSQL
* **ORM**: SQLAlchemy (`asyncpg` driver for async operations)
* **Testing**: `pytest`, `httpx`
* **Dependency Management**: `pip`, `requirements.txt`
* **Containerization**: Docker, Docker Compose

## 3. Getting Started

### Prerequisites

* Python 3.10+
* `pip` (Python package installer)
* Docker and Docker Compose (if running via Docker)
* A Supabase project (for actual JWT and database connection)

### Local Setup

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd mini-sip-tracker-backend
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate # On Windows: .\venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    At the root of the project, create a file named `.env` and add your Supabase credentials:

    ```env
    # .env
    SUPABASE_SECRET_KEY="YOUR_SUPABASE_JWT_SECRET"
    DATABASE_URL="postgresql+asyncpg://YOUR_SUPABASE_USER:YOUR_SUPABASE_PASSWORD@YOUR_SUPABASE_HOST:5432/YOUR_SUPABASE_DB_NAME"
    ```

    * **`SUPABASE_SECRET_KEY`**: You can find this in your Supabase project settings under `API` > `JWT Secret`. Alternatively, for local testing, if you generate a JWT directly (as shown in `auth.py`), use the same secret key you used for signing.
    * **`DATABASE_URL`**: This is your database connection string from Supabase. Go to `Project Settings` > `Database` > `Connection String` > `URI`. Ensure the `asyncpg` driver is used (e.g., `postgresql+asyncpg://...`).

5.  **Run database migrations (on startup):**
    The `main.py` script automatically creates tables when the application starts up (`@app.on_event("startup")`).

6.  **Run the application:**

    ```bash
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    ```

    The API will be accessible at `http://localhost:8000`. The `--reload` flag is useful for development as it restarts the server on code changes. For production, remove this flag.

### Supabase JWT Setup

The application expects a JWT in the `Authorization: Bearer <token>` header. This JWT would typically be issued by Supabase after a user successfully logs in (e.g., via their `supabase-js` client library in a frontend).

For **local testing** without a full frontend, you can generate a mock JWT using the `create_mock_jwt` function provided in `auth.py` (though not for production use).

Example of generating a mock token in a Python console (requires `python-jose` and `python-dotenv`):

```python
import os
from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv

load_dotenv()
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "your-super-secret-supabase-jwt-key")
ALGORITHM = "HS256"

def create_mock_jwt(user_id: str, secret_key: str = SUPABASE_SECRET_KEY) -> str:
    to_encode = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "aud": "authenticated",
        "role": "authenticated"
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

# Replace with your desired test user ID (a valid UUID)
test_user_id = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
mock_token = create_mock_jwt(test_user_id)
print(f"Generated Mock JWT: {mock_token}")
print(f"Test User ID: {test_user_id}")
```
Use the `mock_token` in your API requests as the `Bearer` token.

### Running with Docker Compose

1.  **Ensure Docker is running.**
2.  **Create your `.env` file** as described in the [Local Setup](#local-setup) section. The `docker-compose.yml` is configured to load variables from it.
3.  **Build and run the services:**

    ```bash
    docker-compose up --build
    ```

    * This will build the `web` service (FastAPI app) and start a local PostgreSQL `db` service (optional, primarily for local testing without Supabase).
    * The API will be accessible at `http://localhost:8000`.

4.  **To stop and remove containers:**

    ```bash
    docker-compose down
    ```

## 4. API Usage

You can use tools like `curl`, Postman, Insomnia, or write a Python script with `httpx` to interact with the API.

### Authentication

All protected endpoints require a JWT in the `Authorization` header:

`Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>`

### Create SIP Plan (`POST /sips/`)

Creates a new SIP plan for the authenticated user.

* **URL**: `http://localhost:8000/sips/`
* **Method**: `POST`
* **Headers**:
    * `Content-Type: application/json`
    * `Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>`
* **Request Body**:

    ```json
    {
      "scheme_name": "Parag Parikh Flexi Cap",
      "monthly_amount": 5000,
      "start_date": "2024-01-01"
    }
    ```

* **Example `curl` command:**

    ```bash
    curl -X POST \
      http://localhost:8000/sips/ \
      -H 'Content-Type: application/json' \
      -H 'Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>' \
      -d '{
            "scheme_name": "Parag Parikh Flexi Cap",
            "monthly_amount": 5000,
            "start_date": "2024-01-01"
          }'
    ```

* **Success Response (201 Created):**

    ```json
    {
      "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
      "user_id": "YOUR_USER_ID",
      "scheme_name": "Parag Parikh Flexi Cap",
      "monthly_amount": 5000.0,
      "start_date": "2024-01-01",
      "created_at": "2024-06-06T10:00:00.123456+00:00",
      "updated_at": "2024-06-06T10:00:00.123456+00:00"
    }
    ```

### Get SIP Summary (`GET /sips/summary`)

Returns a summary of SIPs for the authenticated user, grouped by scheme. `total_invested` is calculated as `monthly_amount * months_invested`. `months_invested` is calculated from `start_date` up to the current month.

* **URL**: `http://localhost:8000/sips/summary`
* **Method**: `GET`
* **Headers**:
    * `Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>`

* **Example `curl` command:**

    ```bash
    curl -X GET \
      http://localhost:8000/sips/summary \
      -H 'Authorization: Bearer <YOUR_SUPABASE_JWT_TOKEN>'
    ```

* **Success Response (200 OK):**

    ```json
    [
      {
        "scheme_name": "Parag Parikh Flexi Cap",
        "total_invested": 30000.0,
        "months_invested": 6
      },
      {
        "scheme_name": "Kotak Equity Opportunities",
        "total_invested": 15000.0,
        "months_invested": 5
      }
    ]
    ```

## 5. Running Tests

Unit tests are written using `pytest`.

1.  **Ensure you have a `.env` file** with `SUPABASE_SECRET_KEY` set (it can be any string for testing, as the mock JWT uses this).
2.  **Run tests from the project root:**

    ```bash
    pytest
    ```

    *Note*: The tests use an in-memory or temporary database setup for isolation and will clean up after themselves. They do not interact with your actual Supabase database.

## 6. System Design Document

A detailed system design document (`design.md`) is provided in the project root, covering:
* Database Schema
* APIs and Endpoints (Current & Future)
* Caching Strategies
* Background Tasks (for NAV integration, SIP execution)
* Security & Multi-tenant Architecture (especially with Supabase RLS)
* Bonus: Microservices Layout for Larger Scale

[Open design.md](design.md)

## 7. Assignment Completion Notes

* **SIP Monthly Execution Simulation**: The assignment mentioned simulating monthly SIP execution using `apscheduler` or `celery`. While the `design.md` discusses how this would be implemented as a background task, the provided codebase does not include a live scheduler setup. This is because running a persistent scheduler within the context of a single FastAPI application instance can be complex for a short assignment, and typically requires a separate worker process. The `calculate_sip_summary` function *assumes* monthly investments have occurred up to the current date based on `start_date`.
* **Mock NAVs**: The `total_invested` calculation is based on `monthly_amount * months_invested`. The requirement "Assume mock NAVs to calculate units purchased if needed" is addressed by focusing solely on `total_invested` based on monthly payments, as units are not required for the `total_invested` metric in the summary output. Real NAV integration is discussed in the `design.md`.
* **Supabase Interaction**: The database connection and authentication are set up to be compatible with Supabase's PostgreSQL and JWT. The `.env` file is crucial for connecting to your specific Supabase project. Row-Level Security (RLS) policies on your Supabase tables would be essential in a production environment to fully enforce multi-tenancy at the database level (example RLS policies are given in `design.md`).
