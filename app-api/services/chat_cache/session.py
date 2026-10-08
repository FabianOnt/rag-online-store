import redis
from services.chat_cache.config import settings

chat_cache = redis.Redis(
    host='chat-cache',
    port=6379,
    db=0,
    decode_responses=True,
    password=settings.ADMINPASSWORD
)