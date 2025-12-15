import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# 使用SQLite作为测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库会话"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理数据库
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """测试客户端，覆盖数据库依赖"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # 清理依赖覆盖
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }


@pytest.fixture
def test_user(client, test_user_data):
    """创建并返回测试用户"""
    response = client.post("/auth/register", json=test_user_data)
    return response.json()


@pytest.fixture
def auth_token(client, test_user_data):
    """获取认证token"""
    response = client.post("/auth/login", json={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def test_source_data():
    """测试内容源数据"""
    return {
        "name": "测试RSS源",
        "url": "https://www.ruanyifeng.com/blog/",
        "type": "rss",
        "rss_url": "https://www.ruanyifeng.com/blog/atom.xml",
        "category": "技术",
        "fetch_frequency": 60,
        "is_active": True
    }


@pytest.fixture
def test_source(client, auth_headers, test_source_data):
    """创建测试内容源"""
    response = client.post("/sources", headers=auth_headers, json=test_source_data)
    return response.json()
