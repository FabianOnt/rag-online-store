from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

import os
import services.chat_db.models

with open("/run/secrets/chat_db_non_root_password", "r") as file:
    api_password = file.read()
    file.close()

db_name = os.getenv("CHAT_DB_NAME")
api_user = os.getenv("CHAT_DB_NON_ROOT_USER")


DATABASE_URL = f"postgresql+psycopg2://{api_user}:{api_password}@chat-db:5432/{db_name}"

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