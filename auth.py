# auth.py
import os
from datetime import datetime, timezone
from jose import jwt, JWTError
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase secret key from environment variables
# In a real Supabase setup, this would be your JWT secret or a public key.
# For local development, you might use the anon key or a service role key's JWT secret
# from your Supabase project settings.
# For this assignment, we'll assume a shared secret for simplicity of demonstration.
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "your-super-secret-supabase-jwt-key")
ALGORITHM = "HS256" # Supabase uses HS256 for JWT signing by default

# Initialize HTTPBearer for extracting token from Authorization header
security = HTTPBearer()

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    FastAPI dependency to extract and validate the user_id from a Supabase JWT.

    Args:
        credentials: HTTPAuthorizationCredentials object containing the Bearer token.

    Returns:
        The user ID (sub) from the JWT payload.

    Raises:
        HTTPException: If the token is invalid, expired, or missing required claims.
    """
    token = credentials.credentials
    try:
        # Decode the JWT.
        # audience=None allows for flexible audience validation, but in production,
        # you might want to specify your Supabase project URL here.
        payload = jwt.decode(token, SUPABASE_SECRET_KEY, algorithms=[ALGORITHM], audience=None)

        user_id: str = payload.get("sub") # Supabase uses 'sub' for user ID
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: Missing 'sub' claim")

        # Check for token expiration (Supabase JWTs have an 'exp' claim)
        expiration_timestamp = payload.get("exp")
        if expiration_timestamp is None:
            raise HTTPException(status_code=401, detail="Invalid token: Missing expiration ('exp') claim")

        # Convert expiration timestamp to a datetime object
        expiration_datetime = datetime.fromtimestamp(expiration_timestamp, tz=timezone.utc)
        current_datetime = datetime.now(timezone.utc)

        if current_datetime > expiration_datetime:
            raise HTTPException(status_code=401, detail="Token has expired")

        return user_id
    except JWTError as e:
        # Catch specific JWT errors (e.g., signature mismatch, invalid claims)
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error during token validation: {e}")

# Example of how to generate a mock JWT for testing (NOT for production use)
# This is for local testing purposes to simulate a Supabase JWT.
# In a real scenario, Supabase client-side library generates this.
def create_mock_jwt(user_id: str, secret_key: str = SUPABASE_SECRET_KEY) -> str:
    """
    Creates a mock JWT for testing purposes.
    In a real application, Supabase itself issues these tokens.
    DO NOT use this function in production to issue tokens.
    """
    to_encode = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1), # Token valid for 1 hour
        "aud": "authenticated", # Standard Supabase audience
        "role": "authenticated" # Standard Supabase role
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)
    return encoded_jwt

# Import timedelta for create_mock_jwt, if used for local testing
from datetime import timedelta
