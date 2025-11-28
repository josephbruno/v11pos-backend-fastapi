"""
Pytest configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.product import Product, Category
from app.models.customer import Customer
import uuid


# Use in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a test database and yield a session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with dependency override"""
    def override_get_db():
        return db

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """Create a test user"""
    from app.security import hash_password
    
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        phone="+1234567890",
        password=hash_password("testpassword123"),
        role="staff",
        status="active",
        join_date=datetime.now(),
        permissions=[]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_category(db):
    """Create a test category"""
    category = Category(
        id=str(uuid.uuid4()),
        name="Test Category",
        slug="test-category",
        description="Test category description",
        active=True,
        sort_order=0
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def test_product(db, test_category):
    """Create a test product"""
    product = Product(
        id=str(uuid.uuid4()),
        name="Test Product",
        slug="test-product",
        description="Test product description",
        price=1999,  # $19.99
        cost=999,    # $9.99
        category_id=test_category.id,
        stock=100,
        min_stock=5,
        available=True,
        featured=False,
        department="kitchen",
        preparation_time=15
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@pytest.fixture
def test_customer(db):
    """Create a test customer"""
    customer = Customer(
        id=str(uuid.uuid4()),
        name="Test Customer",
        phone="+9876543210",
        email="customer@example.com",
        address="Test Address",
        loyalty_points=100,
        total_spent=5000,
        visit_count=5,
        is_blacklisted=False
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers with JWT token"""
    from app.security import create_token_pair
    
    token_response = create_token_pair(
        user_id=test_user.id,
        email=test_user.email,
        role=test_user.role
    )
    
    return {
        "Authorization": f"Bearer {token_response.access_token}",
        "Content-Type": "application/json"
    }


from datetime import datetime
