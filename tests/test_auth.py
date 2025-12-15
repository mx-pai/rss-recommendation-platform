"""
用户认证相关的测试
"""
import pytest
from fastapi import status


class TestUserRegistration:
    """测试用户注册功能"""

    def test_register_success(self, client, test_user_data):
        """测试: 用户注册成功"""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "hashed_password" not in data  # 不应暴露密码

    def test_register_duplicate_username(self, client, test_user, test_user_data):
        """测试: 重复用户名注册应失败"""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "已存在" in response.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        """测试: 重复邮箱注册应失败"""
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "test@example.com",  # 已存在的邮箱
            "password": "password123"
        })

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "已存在" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """测试: 无效邮箱格式应失败"""
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "invalid-email",  # 无效邮箱
            "password": "password123"
        })

        # Pydantic会进行邮箱验证
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """测试用户登录功能"""

    def test_login_success(self, client, test_user, test_user_data):
        """测试: 登录成功"""
        response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, test_user, test_user_data):
        """测试: 错误密码登录应失败"""
        response = client.post("/auth/login", json={
            "username": test_user_data["username"],
            "password": "wrongpassword"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试: 不存在的用户登录应失败"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "password123"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_empty_credentials(self, client):
        """测试: 空凭证登录应失败"""
        response = client.post("/auth/login", json={
            "username": "",
            "password": ""
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserAuthentication:
    """测试用户认证功能"""

    def test_get_current_user_success(self, client, auth_headers, test_user_data):
        """测试: 获取当前用户信息成功"""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]

    def test_get_current_user_no_token(self, client):
        """测试: 无token访问应失败"""
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client):
        """测试: 无效token访问应失败"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_expired_token(self, client):
        """测试: 过期token访问应失败"""
        # 假设token已过期 (需要mock时间或使用过期token)
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired"
        response = client.get("/auth/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# TODO: 添加更多测试用例
# - 测试密码强度验证
# - 测试用户名格式验证
# - 测试token刷新功能
# - 测试并发登录
