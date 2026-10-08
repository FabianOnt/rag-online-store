from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import os
from services.store_db.models import ProductSummary, DocumentSearch, ReviewsSearch

with open("/run/secrets/store_db_agent_password", "r") as file:
    agent_password = file.read()
    file.close()

db_name = os.getenv("STORE_DB_NAME")
agent_user = os.getenv("STORE_DB_AGENT_USER")


DATABASE_URL = f"postgresql+psycopg2://{agent_user}:{agent_password}@store-db:5432/{db_name}"

engine = create_engine(
    url=DATABASE_URL, 
    echo=True,
    pool_size=10,
    pool_timeout=30,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()