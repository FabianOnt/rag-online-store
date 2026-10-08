import redis
from fastapi import HTTPException

from services.chat_cache.config import settings

def validate_session_token(cache: redis.Redis, session_token: str) -> bool:
    result = cache.getex(session_token, ex=settings.CHAT_SESSION_TIMEOUT)
    print(result)
    return result