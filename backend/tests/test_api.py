"""FastAPI 端到端接口测试 —— auth / contracts / knowledge / compare / root。

测试策略
--------
用 FastAPI 自带的 TestClient 发送真实 HTTP 请求（不是 mock），
配合 conftest.py 里的内存 SQLite fixtures 做隔离。

接口契约测试矩阵（每个端点至少覆盖 200 / 400 / 401 / 403 / 404）
-----------------------------------------------------------------
Auth 路由（/api/auth/...）
    POST /register   -> 成功注册 / 用户名过短 / 密码过短 / 重复用户名
    POST /login      -> 成功登录拿 JWT / 密码错 401 / 用户不存在 401
    GET  /me         -> token 对返回用户信息 / 无 token 401 / 伪造 token 401

Contracts 路由（/api/contracts/...）
    POST /upload            -> TXT 上传 + 列表可见 + 详情可见 / 非法扩展名 400 / 空内容 400
    GET  /                  -> 列表
    GET  /{id}              -> 正常详情 / 不存在 404
    POST /{id}/versions     -> 上传 v2 版本
    （所有端点都验证未登录 401）

Knowledge 路由（/api/knowledge/...）
    Clause CRUD：admin 全链路创建-读取-更新-删除 / 普通用户写 403 / 不存在 404
    Regulation CRUD：同上
    POST /rebuild-index -> 空库 400 / 有数据 200 / 普通用户 403
    注：GET /clauses 和 GET /regulations 不需要鉴权（public read）

Compare 路由（/api/compare/...）
    POST /text      -> 正常比对返回 summary+diffs / 空文本 400 / 未登录 401
    POST /versions  -> 合同不存在 404

Root
    GET / -> 健康检查

有意跳过的路由
--------------
review / generation / chat / compliance —— 这四个内部调用了 LLM，
用户明确说不测模型相关的，所以这里不覆盖。

如何跑
------
    cd backend
    python3 -m pytest tests/test_api.py -v      # 只跑接口层
    python3 -m pytest tests/ -k "Contracts"     # 只跑合同相关
    python3 -m pytest tests/ -q                 # 简洁模式
"""
import io

import pytest


# ============================================================
# Auth 路由
# ============================================================


class TestAuthRegister:
    """POST /api/auth/register —— 用户注册（无鉴权，任何访客可调用）。"""

    def test_register_success(self, client):
        """正常注册应返回 200 + id + username。"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "newuser", "password": "pass1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "newuser"
        assert "id" in data

    def test_register_short_username(self, client):
        """用户名 < 3 位应返回 400。"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "ab", "password": "pass1234"},
        )
        assert resp.status_code == 400

    def test_register_short_password(self, client):
        """密码 < 6 位应返回 400。"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "longuser", "password": "12345"},
        )
        assert resp.status_code == 400

    def test_register_duplicate_username(self, client, admin_user):
        """已存在的用户名（testadmin 由 admin_user fixture 创建）应返回 400。"""
        resp = client.post(
            "/api/auth/register",
            json={"username": "testadmin", "password": "pass1234"},
        )
        assert resp.status_code == 400


class TestAuthLogin:
    """POST /api/auth/login —— 账号密码登录。"""

    def test_login_success(self, client, admin_user):
        """正确账号密码应返回 200 + access_token + role。"""
        resp = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["role"] == "admin"

    def test_login_wrong_password(self, client, admin_user):
        """密码错误应返回 401，不暴露用户名是否存在。"""
        resp = client.post(
            "/api/auth/login",
            json={"username": "testadmin", "password": "wrongpass"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        """不存在的用户名也返回 401，避免枚举。"""
        resp = client.post(
            "/api/auth/login",
            json={"username": "nobody", "password": "whatever"},
        )
        assert resp.status_code == 401


class TestAuthMe:
    """GET /api/auth/me —— 获取当前登录用户信息（需要 Bearer token）。"""

    def test_me_returns_current_user(self, client, admin_token):
        """有效 token -> 200，返回当前用户的 id / username / role。"""
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testadmin"
        assert data["role"] == "admin"

    def test_me_no_token_401(self, client):
        """完全不带 Authorization 头 -> 401。"""
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_invalid_token_401(self, client):
        """伪造 token 字符串 -> 401（解码失败）。"""
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer fake.token.here"},
        )
        assert resp.status_code == 401


# ============================================================
# Contracts 路由
# ============================================================


class TestContracts:
    """合同管理全流程：上传 TXT -> 列表 -> 详情 -> 新版本。"""

    def test_upload_txt_and_list(self, client, user_token):
        """上传 TXT 合同 -> 列表可见 -> 详情能读回解析后的正文。"""
        txt = io.BytesIO("第一条 甲方应当按时交货。\n第二条 乙方应当按时付款。".encode("utf-8"))
        resp = client.post(
            "/api/contracts/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            data={"title": "测试合同", "contract_type": "买卖合同"},
            files={"file": ("contract.txt", txt, "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "测试合同"
        assert data["version_no"] == 1
        contract_id = data["id"]

        # 列表能看到刚上传的那条
        list_resp = client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert list_resp.status_code == 200
        items = list_resp.json()
        assert len(items) >= 1
        assert any(c["id"] == contract_id for c in items)

        # 详情能看到解析后的正文
        detail_resp = client.get(
            f"/api/contracts/{contract_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["title"] == "测试合同"
        assert "甲方" in detail["content"]

    def test_upload_unsupported_extension(self, client, user_token):
        """非法扩展名（.exe）应返回 400。"""
        bad = io.BytesIO(b"not a real file")
        resp = client.post(
            "/api/contracts/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("bad.exe", bad, "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_empty_content(self, client, user_token):
        """文件里只有空白字符，解析后为空，应返回 400。"""
        empty = io.BytesIO(b"   \n\n  ")
        resp = client.post(
            "/api/contracts/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("empty.txt", empty, "text/plain")},
        )
        assert resp.status_code == 400

    def test_get_nonexistent_contract(self, client, user_token):
        """查一个不存在的合同 id -> 404。"""
        resp = client.get(
            "/api/contracts/99999",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 404

    def test_upload_new_version(self, client, user_token):
        """上传 v1，再上传 v2，version_no 应自增到 2。"""
        v1 = io.BytesIO("第一条 v1 条款。".encode("utf-8"))
        up = client.post(
            "/api/contracts/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("v1.txt", v1, "text/plain")},
        )
        contract_id = up.json()["id"]

        v2 = io.BytesIO("第一条 v2 修改后的条款。".encode("utf-8"))
        v2_resp = client.post(
            f"/api/contracts/{contract_id}/versions",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("v2.txt", v2, "text/plain")},
        )
        assert v2_resp.status_code == 200
        assert v2_resp.json()["version_no"] == 2

    def test_unauthorized_access(self, client):
        """不带 token 访问 /api/contracts -> 401。"""
        resp = client.get("/api/contracts")
        assert resp.status_code == 401


# ============================================================
# Knowledge 路由
# ============================================================


class TestKnowledgeClauses:
    """条款库 CRUD（GET 公开，写操作需要 admin）。"""

    def test_admin_crud_clause(self, client, admin_token):
        """admin 全链路：创建 -> 列表可见 -> 更新 -> 删除。"""
        # Create
        resp = client.post(
            "/api/knowledge/clauses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "保密义务",
                "category": "保密",
                "risk_level": "中",
                "content": "双方对合同内容负有保密义务...",
            },
        )
        assert resp.status_code == 200
        clause_id = resp.json()["id"]

        # List（public read，不需要 token）
        list_resp = client.get("/api/knowledge/clauses")
        assert list_resp.status_code == 200
        assert any(c["id"] == clause_id for c in list_resp.json())

        # Update
        update_resp = client.put(
            f"/api/knowledge/clauses/{clause_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "title": "保密义务（修改）",
                "category": "保密",
                "risk_level": "高",
                "content": "修改后的保密条款内容",
            },
        )
        assert update_resp.status_code == 200

        # Delete
        del_resp = client.delete(
            f"/api/knowledge/clauses/{clause_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200

    def test_normal_user_cannot_write_clause(self, client, user_token):
        """普通 user 角色尝试写条款 -> 403 权限不足。"""
        resp = client.post(
            "/api/knowledge/clauses",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"title": "test", "content": "body"},
        )
        assert resp.status_code == 403

    def test_update_nonexistent_clause(self, client, admin_token):
        """更新不存在的条款 id -> 404。"""
        resp = client.put(
            "/api/knowledge/clauses/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "x", "content": "y"},
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_clause(self, client, admin_token):
        """删除不存在的条款 id -> 404。"""
        resp = client.delete(
            "/api/knowledge/clauses/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestKnowledgeRegulations:
    """法规库 CRUD（与 Clause 共享 require_admin 守卫）。"""

    def test_admin_crud_regulation(self, client, admin_token):
        """admin 创建法规 -> 列表可见 -> 删除。"""
        resp = client.post(
            "/api/knowledge/regulations",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "个人信息保护法",
                "article_no": "第十三条",
                "content": "处理个人信息应当具有明确、合理的目的...",
            },
        )
        assert resp.status_code == 200
        reg_id = resp.json()["id"]

        list_resp = client.get("/api/knowledge/regulations")
        assert list_resp.status_code == 200
        assert any(r["id"] == reg_id for r in list_resp.json())

        del_resp = client.delete(
            f"/api/knowledge/regulations/{reg_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert del_resp.status_code == 200

    def test_normal_user_cannot_write_regulation(self, client, user_token):
        """普通 user 写法规 -> 403。"""
        resp = client.post(
            "/api/knowledge/regulations",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"name": "test", "article_no": "1", "content": "body"},
        )
        assert resp.status_code == 403


class TestRebuildIndex:
    """POST /api/knowledge/rebuild-index —— 全量重建向量索引（仅 admin）。"""

    def test_rebuild_empty_knowledge_400(self, client, admin_token):
        """条款库和法规库都空 -> 400，提示先添加内容。"""
        resp = client.post(
            "/api/knowledge/rebuild-index",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    def test_rebuild_with_data(self, client, admin_token):
        """先加一条条款再重建 -> 200，indexed=1。"""
        client.post(
            "/api/knowledge/clauses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "test", "content": "这是测试条款的正文内容"},
        )
        resp = client.post(
            "/api/knowledge/rebuild-index",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["indexed"] == 1

    def test_rebuild_requires_admin(self, client, user_token):
        """普通用户调 rebuild-index -> 403。"""
        resp = client.post(
            "/api/knowledge/rebuild-index",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403


# ============================================================
# Compare 路由
# ============================================================


class TestCompare:
    """条款比对：直接粘贴文本比对 + 版本间比对。"""

    def test_compare_texts_success(self, client, user_token):
        """两份不同文本比对 -> 200，返回 summary 和 diffs 结构。"""
        resp = client.post(
            "/api/compare/text",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "text_a": "第一条 甲方应当按时交货。\n第二条 乙方应当按时付款。",
                "text_b": "第一条 甲方应当在三十日内交货。\n第二条 乙方应当按时付款。",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "summary" in data
        assert "diffs" in data
        assert isinstance(data["summary"], dict)
        assert isinstance(data["diffs"], list)

    def test_compare_texts_empty_input(self, client, user_token):
        """任意一侧为空字符串 -> 400。"""
        resp = client.post(
            "/api/compare/text",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"text_a": "", "text_b": "something"},
        )
        assert resp.status_code == 400

    def test_compare_texts_unauthorized(self, client):
        """不带 token 调 compare -> 401。"""
        resp = client.post(
            "/api/compare/text",
            json={"text_a": "a", "text_b": "b"},
        )
        assert resp.status_code == 401

    def test_compare_versions_not_found(self, client, user_token):
        """对比不存在的合同 id -> 404。"""
        resp = client.post(
            "/api/compare/versions",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"contract_id": 99999, "version_a": 1, "version_b": 2},
        )
        assert resp.status_code == 404


# ============================================================
# Root 路由
# ============================================================


def test_root_endpoint(client):
    """GET / 健康检查 -> 200，返回 app 名称和 docs 路径。"""
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert "app" in body
    assert "docs" in body
