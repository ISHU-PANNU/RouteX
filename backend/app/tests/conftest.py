import os
# Set environment to testing before any other settings/app loads
os.environ["ENV"] = "testing"

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.config import settings
from app.database.base import Base
from app.dependencies.db import get_db
from app.main import app
from app.models.user import User, UserRole
from app.core import security

# SQLite in-memory test database URL
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
    # Ensure fresh table setups
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine) -> Generator:
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db) -> Generator:
    # Override get_db with test database session
    def override_get_db():
        try:
            yield db
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_users(db) -> dict:
    pwd = "SecurePassword123!"
    h = security.get_password_hash(pwd)
    
    customer = User(
        name="Test Customer",
        email="customer@example.com",
        password_hash=h,
        phone="+15550199",
        role=UserRole.Customer
    )
    agent = User(
        name="Test Driver",
        email="driver@example.com",
        password_hash=h,
        phone="+15550299",
        role=UserRole.DeliveryAgent
    )
    admin = User(
        name="Test Admin",
        email="admin@example.com",
        password_hash=h,
        phone="+15550399",
        role=UserRole.Admin
    )
    
    db.add(customer)
    db.add(agent)
    db.add(admin)
    db.commit()
    db.refresh(customer)
    db.refresh(agent)
    db.refresh(admin)
    
    return {
        "customer": customer,
        "agent": agent,
        "admin": admin,
        "password": pwd
    }

@pytest.fixture(scope="function")
def customer_headers(test_users) -> dict:
    user = test_users["customer"]
    token = security.create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def agent_headers(test_users) -> dict:
    user = test_users["agent"]
    token = security.create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def admin_headers(test_users) -> dict:
    user = test_users["admin"]
    token = security.create_access_token(subject=user.id, role=user.role.value)
    return {"Authorization": f"Bearer {token}"}
