import os
from pathlib import Path

class Settings:
    ADMIN_API_KEY: str = Path(f"/run/secrets/app_api_admin_key").read_text().strip()

settings = Settings()