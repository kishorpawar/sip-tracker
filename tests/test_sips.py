# tests/test_sips.py
import pytest
from httpx import AsyncClient
from main import app
from database import get_db, engine, Base, AsyncSessionLocal
from models import SIPPlan
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from auth import create_mock_jwt, SUPABASE_SECRET_KEY
import os
import asyncio

# Define a test user ID
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
# Generate a mock JWT for the test user
TEST_JWT_TOKEN = create_mock_jwt(TEST_USER_ID, SUPABASE_SECRET_KEY)
TEST_HEADERS = {"Authorization": f"Bearer {TEST_JWT_TOKEN}"}

# Override the get_db dependency for testing
@pytest.fixture(name="db_session")
async def db_session_fixture():
    """
    Provides a clean, independent database session for each test.
    Rolls back transactions after each test to ensure test isolation.
    """
    # Create the database tables for testing
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Use a separate session for tests
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # Clean up: drop all tables after tests or rollback for transaction isolation
            # For this simple test, we'll drop and recreate tables to ensure isolation
            await session.close()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(name="client")
async def client_fixture(db_session: AsyncSession):
    """
    Provides an asynchronous test client for the FastAPI app.
    Overrides the get_db dependency to use the test session.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides = {} # Clean up overrides


@pytest.mark.asyncio
async def test_create_sip_plan(client: AsyncClient):
    """
    Test case for creating a new SIP plan.
    """
    sip_data = {
        "scheme_name": "Axis Bluechip Fund",
        "monthly_amount": 7500.00,
        "start_date": "2023-03-15"
    }
    response = await client.post("/sips/", json=sip_data, headers=TEST_HEADERS)

    assert response.status_code == 201
    created_sip = response.json()
    assert created_sip["scheme_name"] == sip_data["scheme_name"]
    assert created_sip["monthly_amount"] == sip_data["monthly_amount"]
    assert created_sip["user_id"] == TEST_USER_ID
    assert "id" in created_sip
    assert "created_at" in created_sip

    # Verify that the SIP was actually saved in the database
    db_session: AsyncSession = app.dependency_overrides[get_db]()
    result = await db_session.execute(select(SIPPlan).filter_by(id=created_sip["id"]))
    sip_in_db = result.scalars().first()
    assert sip_in_db is not None
    assert str(sip_in_db.user_id) == TEST_USER_ID # UUID comparison
    assert sip_in_db.scheme_name == "Axis Bluechip Fund"


@pytest.mark.asyncio
async def test_get_sip_summary_no_sips(client: AsyncClient):
    """
    Test case for getting SIP summary when no SIPs exist for the user.
    """
    response = await client.get("/sips/summary", headers=TEST_HEADERS)
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_sip_summary_with_sips(client: AsyncClient, db_session: AsyncSession):
    """
    Test case for getting SIP summary with existing SIPs.
    """
    # Create some mock SIPs directly in the database for the test user
    from uuid import UUID
    user_uuid = UUID(TEST_USER_ID)

    sip1 = SIPPlan(
        user_id=user_uuid,
        scheme_name="Parag Parikh Flexi Cap",
        monthly_amount=5000.00,
        start_date=date(2024, 1, 1) # Jan, Feb, Mar, Apr, May, June (6 months if today is June 2025)
    )
    sip2 = SIPPlan(
        user_id=user_uuid,
        scheme_name="Parag Parikh Flexi Cap",
        monthly_amount=2000.00,
        start_date=date(2024, 3, 1) # Mar, Apr, May, June (4 months if today is June 2025)
    )
    sip3 = SIPPlan(
        user_id=user_uuid,
        scheme_name="Kotak Equity Opportunities",
        monthly_amount=3000.00,
        start_date=date(2024, 2, 1) # Feb, Mar, Apr, May, June (5 months if today is June 2025)
    )

    db_session.add_all([sip1, sip2, sip3])
    await db_session.commit()

    response = await client.get("/sips/summary", headers=TEST_HEADERS)
    assert response.status_code == 200
    summary = response.json()

    # Get today's date for calculation context
    today = date.today()
    # Calculate expected months based on today's date
    months_from_jan = (today.year - 2024) * 12 + (today.month - 1) + 1
    months_from_feb = (today.year - 2024) * 12 + (today.month - 2) + 1
    months_from_mar = (today.year - 2024) * 12 + (today.month - 3) + 1

    expected_summary = [
        {
            "scheme_name": "Parag Parikh Flexi Cap",
            "total_invested": (5000 * months_from_jan) + (2000 * months_from_mar),
            "months_invested": months_from_jan # max months for the scheme
        },
        {
            "scheme_name": "Kotak Equity Opportunities",
            "total_invested": 3000 * months_from_feb,
            "months_invested": months_from_feb
        }
    ]

    # Sort summaries for consistent comparison, as order might not be guaranteed
    summary.sort(key=lambda x: x["scheme_name"])
    expected_summary.sort(key=lambda x: x["scheme_name"])

    assert len(summary) == 2
    # Use pytest.approx for float comparisons
    assert summary[0]["scheme_name"] == expected_summary[0]["scheme_name"]
    assert summary[0]["total_invested"] == pytest.approx(expected_summary[0]["total_invested"])
    assert summary[0]["months_invested"] == expected_summary[0]["months_invested"]

    assert summary[1]["scheme_name"] == expected_summary[1]["scheme_name"]
    assert summary[1]["total_invested"] == pytest.approx(expected_summary[1]["total_invested"])
    assert summary[1]["months_invested"] == expected_summary[1]["months_invested"]


@pytest.mark.asyncio
async def test_unauthenticated_access(client: AsyncClient):
    """
    Test case for unauthenticated access to protected endpoints.
    """
    # Test POST /sips/
    sip_data = {
        "scheme_name": "HDFC Sensex Fund",
        "monthly_amount": 1000.00,
        "start_date": "2024-05-01"
    }
    response = await client.post("/sips/", json=sip_data) # No headers
    assert response.status_code == 403 # HTTPBearer returns 403 Forbidden for missing token

    # Test GET /sips/summary
    response = await client.get("/sips/summary") # No headers
    assert response.status_code == 403

