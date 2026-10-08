from pathlib import Path

class Settings:
    CACHE_TIMEOUT: int = 120
    CHAT_SESSION_TIMEOUT: int = 5*60
    ADMINPASSWORD: str = Path("/run/secrets/chat_cache_password").read_text().strip()

settings = Settings()