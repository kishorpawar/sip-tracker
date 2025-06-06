# models.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Numeric, Date, DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base

class SIPPlan(Base):
    """
    SQLAlchemy model for the 'sips' table.
    Represents a single Systematic Investment Plan (SIP) created by a user.
    """
    __tablename__ = "sips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True) # Link to the Supabase user ID
    scheme_name = Column(String, nullable=False)
    monthly_amount = Column(Numeric(10, 2), nullable=False) # Store up to 2 decimal places
    start_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<SIPPlan(id={self.id}, user_id={self.user_id}, scheme_name='{self.scheme_name}')>"

