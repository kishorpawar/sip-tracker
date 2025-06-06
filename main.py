# main.py
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime, date, timezone
from uuid import UUID

# Import modules from our project
from database import get_db, engine, Base
from models import SIPPlan
from schemas import SIPCreate, SIPResponse, SIPSummary
from auth import get_current_user_id
import crud

# Initialize FastAPI app
app = FastAPI(
    title="Mini SIP Tracker API",
    description="A backend for tracking Systematic Investment Plans (SIPs) with user authentication.",
    version="1.0.0",
)

# Event handler for application startup
@app.on_event("startup")
async def startup_event():
    """
    Event handler that runs when the FastAPI application starts up.
    It creates all necessary database tables based on SQLAlchemy models.
    """
    async with engine.begin() as conn:
        # Drop all tables and recreate them. Use with caution in production!
        # This is good for development/testing to ensure a clean slate.
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created/checked.")

# Root endpoint for basic health check
@app.get("/")
async def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to Mini SIP Tracker API!"}

@app.post(
    "/sips/",
    response_model=SIPResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new SIP plan",
    description="Allows an authenticated user to create a new Systematic Investment Plan.",
)
async def create_sip(
    sip: SIPCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Endpoint to create a new SIP plan for the authenticated user.

    - **sip**: The SIP plan details from the request body.
    - **db**: Database session dependency.
    - **user_id**: Authenticated user's ID injected by the JWT dependency.
    """
    try:
        # Convert user_id string to UUID for the model
        sip_plan = await crud.create_sip_plan(db=db, sip=sip, user_id=user_id)
        # Convert datetime objects to ISO format strings for response
        return SIPResponse(
            id=sip_plan.id,
            user_id=sip_plan.user_id,
            scheme_name=sip_plan.scheme_name,
            monthly_amount=float(sip_plan.monthly_amount), # Convert Decimal to float for Pydantic
            start_date=sip_plan.start_date,
            created_at=sip_plan.created_at.isoformat(),
            updated_at=sip_plan.updated_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SIP: {e}"
        )


@app.get(
    "/sips/summary",
    response_model=List[SIPSummary],
    summary="Get SIP summary for the authenticated user",
    description="Retrieves a summary of all SIPs for the authenticated user, grouped by scheme.",
)
async def get_sip_summary(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Endpoint to get a summary of SIPs for the authenticated user.

    - **db**: Database session dependency.
    - **user_id**: Authenticated user's ID injected by the JWT dependency.
    """
    try:
        sips = await crud.get_user_sips(db=db, user_id=user_id)
        if not sips:
            return [] # Return empty list if no SIPs found for the user

        summary = crud.calculate_sip_summary(sips)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SIP summary: {e}"
        )


if __name__ == "__main__":
    # Ensure environment variables are loaded for local testing
    from dotenv import load_dotenv
    load_dotenv()
    # Run the FastAPI application using Uvicorn
    # Host '0.0.0.0' makes it accessible from outside the container in Docker setup
    uvicorn.run(app, host="0.0.0.0", port=8000)

