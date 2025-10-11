"""
Test authentication service.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user(db_session):
    """Test user creation."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
        full_name="Test User"
    )
    
    user = AuthService.create_user(db_session, user_data)
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.is_active == True
    assert user.hashed_password != "password123"  # Should be hashed


def test_authenticate_user(db_session):
    """Test user authentication."""
    # Create user
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    AuthService.create_user(db_session, user_data)
    
    # Authenticate with correct credentials
    user = AuthService.authenticate_user(db_session, "testuser", "password123")
    assert user is not None
    assert user.username == "testuser"
    
    # Authenticate with wrong password
    user = AuthService.authenticate_user(db_session, "testuser", "wrongpassword")
    assert user is None


def test_get_user_by_email(db_session):
    """Test getting user by email."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )
    created_user = AuthService.create_user(db_session, user_data)
    
    user = AuthService.get_user_by_email(db_session, "test@example.com")
    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test@example.com"
