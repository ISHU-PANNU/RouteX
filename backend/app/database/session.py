from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import settings

db_url = settings.get_db_url()

# Enable check_same_thread = False only for SQLite fallback database engine
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
