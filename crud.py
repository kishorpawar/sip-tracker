# crud.py
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Numeric, Date
from models import SIPPlan
from schemas import SIPCreate
from typing import List, Dict, Any
import math

async def create_sip_plan(db: AsyncSession, sip: SIPCreate, user_id: str) -> SIPPlan:
    """
    Creates a new SIP plan in the database for a given user.

    Args:
        db: The asynchronous database session.
        sip: The Pydantic model containing SIP plan details.
        user_id: The ID of the user creating the SIP.

    Returns:
        The newly created SIPPlan SQLAlchemy model instance.
    """
    # Convert user_id string to UUID for database compatibility
    # Ensure user_id from auth is a valid UUID string
    from uuid import UUID
    user_uuid = UUID(user_id)

    db_sip = SIPPlan(
        user_id=user_uuid,
        scheme_name=sip.scheme_name,
        monthly_amount=sip.monthly_amount,
        start_date=sip.start_date
    )
    db.add(db_sip)
    await db.commit()
    await db.refresh(db_sip) # Refresh to get auto-generated fields like id, created_at
    return db_sip

async def get_user_sips(db: AsyncSession, user_id: str) -> List[SIPPlan]:
    """
    Retrieves all SIP plans for a specific user.

    Args:
        db: The asynchronous database session.
        user_id: The ID of the user whose SIPs are to be retrieved.

    Returns:
        A list of SIPPlan SQLAlchemy model instances.
    """
    # Convert user_id string to UUID
    from uuid import UUID
    user_uuid = UUID(user_id)

    result = await db.execute(
        select(SIPPlan).filter(SIPPlan.user_id == user_uuid)
    )
    sips = result.scalars().all()
    return sips

def calculate_sip_summary(sips: List[SIPPlan]) -> List[Dict[str, Any]]:
    """
    Calculates the SIP summary (total invested, months invested)
    from a list of SIP plans, grouped by scheme name.

    Args:
        sips: A list of SIPPlan SQLAlchemy model instances for a user.

    Returns:
        A list of dictionaries, each representing a SIP summary for a scheme.
        Format: [{"scheme_name": "...", "total_invested": ..., "months_invested": ...}]
    """
    summary_by_scheme = {}
    current_date = date.today()

    for sip in sips:
        # Calculate months invested
        # This assumes SIPs are invested at the start of the month.
        # It counts full months from start_date up to and including the current month.
        months_invested = (current_date.year - sip.start_date.year) * 12 + \
                          (current_date.month - sip.start_date.month) + 1

        # Ensure months_invested is not negative if start_date is in the future
        months_invested = max(0, months_invested)

        # Calculate total invested for this specific SIP
        total_invested_for_sip = float(sip.monthly_amount) * months_invested

        # Aggregate into summary by scheme name
        if sip.scheme_name not in summary_by_scheme:
            summary_by_scheme[sip.scheme_name] = {
                "scheme_name": sip.scheme_name,
                "total_invested": 0.0,
                "months_invested": 0
            }
        
        # Accumulate total invested and average months invested (or max, depending on interpretation)
        # For 'months_invested' in summary, it's typically the average or max for that scheme across all plans
        # If multiple SIPs for the same scheme, the summary 'months_invested' might be tricky.
        # Let's assume 'months_invested' in the summary represents the max months invested for any SIP under that scheme,
        # or simply the count of months an *active* SIP has been running if there's only one.
        # Given the example output `months_invested: 5`, it suggests a simple sum or average isn't directly applicable
        # across multiple SIP plans for the same scheme.
        # For simplicity and aligning with the output format, if multiple SIPs for the same scheme exist,
        # we'll sum the 'total_invested' and just take the maximum 'months_invested' for that scheme.
        # Or, more robustly, if the summary is truly per-scheme, we should sum total invested and
        # perhaps report the *earliest* start date's months_invested, or max.
        # Let's sum total_invested and take the max months_invested for the scheme.

        summary_by_scheme[sip.scheme_name]["total_invested"] += total_invested_for_sip
        summary_by_scheme[sip.scheme_name]["months_invested"] = \
            max(summary_by_scheme[sip.scheme_name]["months_invested"], months_invested)

    # Convert dictionary values to a list
    return list(summary_by_scheme.values())

