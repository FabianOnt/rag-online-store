from pathlib import Path
import os

class Settings:
    ADMIN_API_KEY: str = Path(f"/run/secrets/api_key").read_text().strip()

settings = Settings()