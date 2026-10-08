from fastapi import FastAPI
from routes import admin

app = FastAPI(
    title="Embedding service",
    version="1.0.0"
)
app.include_router(admin.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}