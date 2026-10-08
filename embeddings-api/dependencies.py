from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from config import settings

api_key_header = APIKeyHeader(name="Admin-API-Key", auto_error=False)

def verify_admin_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Admin API Key",
        )
    return api_key