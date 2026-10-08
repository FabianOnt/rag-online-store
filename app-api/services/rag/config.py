class Settings:
    BASE_URL: str = "http://ollama-lb:11434"
    MODEL_NAME: str = "qwen3.5:4b-mlx"
    NUM_PAST_MESSAGES: int = 6


settings = Settings()