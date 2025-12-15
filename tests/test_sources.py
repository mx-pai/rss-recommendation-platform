"""
内容源管理相关的测试
"""
import pytest
from fastapi import status


class TestSourceCreation:
    """测试内容源创建功能"""

    def test_create_source_success(self, client, auth_headers, test_source_data):
        """测试: 创建内容源成功"""
        response = client.post("/sources", headers=auth_headers, json=test_source_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == test_source_data["name"]
        assert data["url"] == test_source_data["url"]
        assert data["type"] == test_source_data["type"]
        assert "id" in data
        assert "user_id" in data

    def test_create_source_without_auth(self, client, test_source_data):
        """测试: 未认证创建内容源应失败"""
        response = client.post("/sources", json=test_source_data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_source_missing_required_fields(self, client, auth_headers):
        """测试: 缺少必需字段应失败"""
        response = client.post("/sources", headers=auth_headers, json={
            "name": "测试源"
            # 缺少 url 和 type
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_multiple_sources(self, client, auth_headers):
        """测试: 创建多个内容源"""
        sources = [
            {"name": "源1", "url": "https://example1.com", "type": "rss"},
            {"name": "源2", "url": "https://example2.com", "type": "manual"},
        ]

        for source_data in sources:
            response = client.post("/sources", headers=auth_headers, json=source_data)
            assert response.status_code == status.HTTP_200_OK


class TestSourceRetrieval:
    """测试内容源获取功能"""

    def test_list_sources_empty(self, client, auth_headers):
        """测试: 获取空源列表"""
        response = client.get("/sources", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_sources_with_data(self, client, auth_headers, test_source):
        """测试: 获取源列表"""
        response = client.get("/sources", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert data[0]["id"] == test_source["id"]

    def test_get_source_by_id(self, client, auth_headers, test_source):
        """测试: 通过ID获取单个源"""
        source_id = test_source["id"]
        response = client.get(f"/sources/{source_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == source_id
        assert data["name"] == test_source["name"]

    def test_get_nonexistent_source(self, client, auth_headers):
        """测试: 获取不存在的源应返回404"""
        response = client.get("/sources/99999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_user_isolation(self, client, test_source):
        """测试: 用户隔离 - 不能访问其他用户的源"""
        # 创建另一个用户
        client.post("/auth/register", json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "pass123"
        })

        # 另一个用户登录
        login_response = client.post("/auth/login", json={
            "username": "otheruser",
            "password": "pass123"
        })
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # 尝试访问第一个用户的源
        response = client.get(f"/sources/{test_source['id']}", headers=other_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSourceUpdate:
    """测试内容源更新功能"""

    def test_update_source_name(self, client, auth_headers, test_source):
        """测试: 更新源名称"""
        source_id = test_source["id"]
        response = client.put(
            f"/sources/{source_id}",
            headers=auth_headers,
            json={"name": "新名称"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == "新名称"

    def test_update_source_multiple_fields(self, client, auth_headers, test_source):
        """测试: 更新多个字段"""
        source_id = test_source["id"]
        update_data = {
            "name": "更新后的名称",
            "category": "新闻",
            "fetch_frequency": 120
        }
        response = client.put(
            f"/sources/{source_id}",
            headers=auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["category"] == update_data["category"]

    def test_update_nonexistent_source(self, client, auth_headers):
        """测试: 更新不存在的源应失败"""
        response = client.put(
            "/sources/99999",
            headers=auth_headers,
            json={"name": "新名称"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSourceDeletion:
    """测试内容源删除功能"""

    def test_delete_source(self, client, auth_headers, test_source):
        """测试: 删除源"""
        source_id = test_source["id"]
        response = client.delete(f"/sources/{source_id}", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK

        # 验证已删除
        get_response = client.get(f"/sources/{source_id}", headers=auth_headers)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_source(self, client, auth_headers):
        """测试: 删除不存在的源"""
        response = client.delete("/sources/99999", headers=auth_headers)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestSourceFetch:
    """测试内容源抓取功能"""

    @pytest.mark.skip(reason="需要mock爬虫服务")
    def test_fetch_from_source(self, client, auth_headers, test_source):
        """测试: 从源抓取内容"""
        source_id = test_source["id"]
        response = client.post(f"/sources/{source_id}/fetch", headers=auth_headers)

        # 注意: 实际测试需要mock爬虫服务
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.skip(reason="需要mock AI服务")
    def test_fetch_with_ai(self, client, auth_headers, test_source):
        """测试: 使用AI富化抓取"""
        source_id = test_source["id"]
        response = client.post(
            f"/sources/{source_id}/fetch?use_ai=true",
            headers=auth_headers
        )

        # 注意: 实际测试需要mock AI服务
        assert response.status_code == status.HTTP_200_OK


# TODO: 添加更多测试用例
# - 测试源分页
# - 测试源筛选
# - 测试源激活/停用
# - 测试批量删除
