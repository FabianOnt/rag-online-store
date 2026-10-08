from fastapi import FastAPI
from routes import customer, admin


app = FastAPI(
    title="E-Commerce RAG API",
    version="1.0.0"
)

app.include_router(customer.router)
app.include_router(admin.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}