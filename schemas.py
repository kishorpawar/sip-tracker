# schemas.py
from datetime import date
from typing import List
from pydantic import BaseModel, Field
from uuid import UUID

class SIPCreate(BaseModel):
    """
    Pydantic schema for creating a new SIP plan.
    Used for the request body of POST /sips/.
    """
    scheme_name: str = Field(..., example="Parag Parikh Flexi Cap", min_length=1, max_length=100)
    monthly_amount: float = Field(..., gt=0, example=5000.00, description="Monthly investment amount, must be greater than 0.")
    start_date: date = Field(..., example="2024-01-01", description="The date the SIP started or will start.")

class SIPResponse(BaseModel):
    """
    Pydantic schema for returning a single SIP plan.
    """
    id: UUID
    user_id: UUID
    scheme_name: str
    monthly_amount: float
    start_date: date
    created_at: str # Use string for datetime in response for simplicity, or datetime object.
    updated_at: str # Use string for datetime in response for simplicity, or datetime object.

    class Config:
        from_attributes = True # Allow Pydantic to create model from SQLAlchemy model attributes

class SIPSummary(BaseModel):
    """
    Pydantic schema for the SIP summary.
    Used for the response body of GET /sips/summary.
    """
    scheme_name: str = Field(..., example="Parag Parikh Flexi Cap")
    total_invested: float = Field(..., example=25000.00)
    months_invested: int = Field(..., example=5)

    class Config:
        from_attributes = True # Not strictly necessary if manually constructing, but good practice.
