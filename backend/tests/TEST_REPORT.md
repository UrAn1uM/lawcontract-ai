# 智能法律合同审查与生成系统 —— 后端测试报告

> 生成时间：2026-09-09
> 测试框架：pytest 9.1.1 + FastAPI TestClient
> 运行命令：`cd backend && python3 -m pytest tests/ -v`

---

## 一、执行总览

| 指标 | 数值 |
|------|------|
| 总用例数 | **66** |
| 通过 | **66** ✅ |
| 失败 | **0** |
| 错误 | **0** |
| 跳过 | **0** |
| 执行耗时 | 13.85s |
| 通过率 | **100%** |

### 按模块分布

| 模块 | 文件 | 用例数 | 类型 |
|------|------|--------|------|
| 安全模块 | `test_security.py` | 11 | 单元测试 |
| 合同切分 | `test_splitter.py` | 7 | 单元测试 |
| 文档解析 | `test_document_parser.py` | 4 | 单元测试 |
| 向量存储 | `test_vector_store.py` | 5 | 单元测试 |
| 条款比对 | `test_compare_service.py` | 9 | 单元测试 |
| API 接口 | `test_api.py` | 30 | 集成测试 |
| **合计** | **7 个文件** | **66** | — |

---

## 二、测试架构

### 技术栈

- **测试框架**：pytest 9.1.1
- **接口测试**：FastAPI TestClient（基于 Starlette，同步发送真实 HTTP 请求）
- **数据库**：SQLite 内存库（`sqlite:///:memory:` + `StaticPool`）
- **向量检索**：NumPy 降级路径（无需 faiss-cpu / sentence-transformers）
- **Fixture 共享**：`conftest.py` 提供全局 fixtures

### 隔离策略

1. **每个测试独立内存库** —— `db_session` fixture 在 yield 前 `create_all`，yield 后 `drop_all`，互不污染，也不会在磁盘生成 `dev.db`
2. **依赖覆盖** —— `app.dependency_overrides[get_db]` 把路由里的 DB 会话替换成 fixture 提供的 `db_session`，绕过 FastAPI lifespan 里的 `init_db()`
3. **无外部依赖** —— 不调用 LLM、不连外网、不读写真实向量目录，所有 RAG 路径走 jieba+MD5 哈希降级

### Fixtures 依赖链

```
db_session ──▶ client / admin_user / normal_user
                  │
                  ▼
          admin_token / user_token （自动登录拿 JWT）
```

| Fixture | 说明 |
|---------|------|
| `db_session` | 独立内存 SQLite 会话，每个测试全新表结构 |
| `client` | FastAPI TestClient，`get_db` 已覆盖 |
| `admin_user` | username=`testadmin` / password=`admin123` / role=`admin` |
| `normal_user` | username=`testuser` / password=`user123` / role=`user` |
| `admin_token` | admin 登录后的 JWT |
| `user_token` | 普通用户登录后的 JWT |

### 有意跳过的模块

以下路由内部调用了 LLM，按需求不纳入本次测试：

| 路由 | 原因 |
|------|------|
| `/api/review/*` | 合同审查 → 调用 LLM 生成风险报告 |
| `/api/generation/*` | 合同生成 → 调用 LLM 起草条款 |
| `/api/chat/*` | 智能问答 → 调用 LLM 对话 |
| `/api/compliance/*` | 合规检查 → 调用 LLM 比对法规 |

---

## 三、详细测试清单

### 3.1 安全模块 — `app/core/security.py`

| # | 用例 | 类型 | 说明 |
|---|------|------|------|
| 1 | `TestPasswordHash::test_hash_format` | Hash 格式 | 验证输出为 `32hex$64hex`（salt + digest） |
| 2 | `TestPasswordHash::test_verify_correct` | 验证 | 正确密码 → True |
| 3 | `TestPasswordHash::test_verify_wrong` | 验证 | 错误密码 → False |
| 4 | `TestPasswordHash::test_verify_empty_stored` | 边界 | 空字符串存储 → False（不崩溃） |
| 5 | `TestPasswordHash::test_verify_bad_format` | 边界 | 格式非法哈希 → False |
| 6 | `TestPasswordHash::test_hash_deterministic_for_same_input` | 加盐特性 | 同一密码 hash 两次结果不同，但 verify 都能过 |
| 7 | `TestJWT::test_round_trip` | 往返 | 签发 → 解码拿回 username |
| 8 | `TestJWT::test_decode_expired_raises` | 安全 | 过期 token → 抛异常 |
| 9 | `TestJWT::test_decode_invalid_token_raises` | 安全 | 伪造字符串 → 抛异常 |
| 10 | `TestJWT::test_decode_wrong_secret_raises` | 安全 | 错误密钥签发 → 签名校验失败 |
| 11 | `TestJWT::test_token_different_users` | 隔离 | 不同 username token 互不干扰 |

**被测函数**：`hash_password` / `verify_password` / `create_access_token` / `decode_token`

---

### 3.2 合同切分 — `app/rag/splitter.py`

| # | 用例 | 类型 | 说明 |
|---|------|------|------|
| 1 | `test_chinese_clause_numbering` | 正常 | 标准中文数字「第一/二/三条」切分，前言 + 3 条 |
| 2 | `test_arabic_clause_numbering` | 兜底 | 阿拉伯数字「1./2.」不匹配正则，走空行分段 |
| 3 | `test_mixed_chinese_arabic` | 正则 | 混合数字「第1条/第10条」正确匹配 |
| 4 | `test_empty_text` | 边界 | 空字符串 / None / 纯空白 → 返回 [] |
| 5 | `test_no_clause_pattern_fallback` | 兜底 | 无条款编号协议 → 按空行分段，编号补「段落N」 |
| 6 | `test_long_numbering` | 正则 | 长编号「第一百零二条」完整保留 |
| 7 | `test_three_paragraph_protocol` | 场景 | 三方投资协议完整场景验证 |

**被测函数**：`split_contract(text: str) -> list[dict]`

---

### 3.3 文档解析 — `app/services/document_parser.py`

| # | 用例 | 类型 | 说明 |
|---|------|------|------|
| 1 | `test_parse_txt` | TXT | 标准英文换行 → 原封不动读回 |
| 2 | `test_parse_txt_chinese` | TXT | 中文合同 UTF-8 不丢失 |
| 3 | `test_parse_docx` | DOCX | python-docx 构造 → 段落抽取正常 |
| 4 | `test_parse_unsupported_extension` | 边界 | 不支持的扩展名 → 抛 ValueError |

**被测函数**：`parse_document(path: str) -> str`
**临时文件**：测试用 `tempfile.NamedTemporaryFile` 在 `/tmp` 生成，结束自动清理

---

### 3.4 向量存储 — `app/rag/vector_store.py`

| # | 用例 | 类型 | 说明 |
|---|------|------|------|
| 1 | `test_build_and_search_basic` | 正常 | 3 条条款小库，查询「权利义务」命中第 1 条，分数 0~1 |
| 2 | `test_search_top_k_greater_than_size` | 边界 | top_k=10 但库只有 3 条 → 截断到 3 |
| 3 | `test_empty_store_search` | 边界 | 空 VectorStore → 返回 [] |
| 4 | `test_save_and_load_round_trip` | 持久化 | 保存到磁盘 → 重新 load → 向量几乎一致（浮点容忍） |
| 5 | `test_load_non_existent_dir` | 边界 | 指向不存在目录 → 返回空库（size=0, vectors=None） |

**被测类**：`VectorStore` —— `build` / `search` / `save` / `load`
**降级路径**：faiss-cpu 不可用时走 NumPy 矩阵乘法算余弦相似度

---

### 3.5 条款比对 — `app/services/compare_service.py`

| # | 用例 | 类型 | 说明 |
|---|------|------|------|
| 1 | `TestCosine::test_identical_vectors` | 余弦 | [1,0,0] vs [1,0,0] → 1.0 |
| 2 | `TestCosine::test_orthogonal_vectors` | 余弦 | [1,0,0] vs [0,1,0] → 0.0（正交） |
| 3 | `TestCosine::test_opposite_vectors` | 余弦 | [1,0] vs [-1,0] → -1.0（方向相反） |
| 4 | `TestCosine::test_zero_vector` | 边界 | 零向量 → 安全返回 0（分母为 0 也不崩溃） |
| 5 | `test_compare_identical_contracts` | 比对 | 两份完全相同 → 所有条款标记「未变」 |
| 6 | `test_compare_one_side_empty` | 比对 | A 侧有内容、B 侧空 → 标记「删除」 |
| 7 | `test_compare_both_empty` | 边界 | 两侧都空 → diffs=[]，summary 全 0 |
| 8 | `test_compare_partial_match` | 比对 | 一条改了措辞、一条没改 → 至少一个「未变」 |
| 9 | `test_compare_diffs_have_required_fields` | 结构 | diffs 每条必须有固定字段，type 只能是五种合法值 |

**被测函数**：`_cosine` / `compare_texts`
**比对三层逻辑**：切分 → `difflib.SequenceMatcher` 对齐（<0.35 视为增删）→ 余弦看语义变化（>0.15 判定为语义修改）

---

### 3.6 API 接口 — `app/api/routes/*.py`

#### Auth 路由

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 1 | `TestAuthRegister::test_register_success` | `/api/auth/register` | POST | 正常注册 → 200 + id + username |
| 2 | `TestAuthRegister::test_register_short_username` | `/api/auth/register` | POST | 用户名 < 3 位 → **400** |
| 3 | `TestAuthRegister::test_register_short_password` | `/api/auth/register` | POST | 密码 < 6 位 → **400** |
| 4 | `TestAuthRegister::test_register_duplicate_username` | `/api/auth/register` | POST | 重复用户名 → **400** |
| 5 | `TestAuthLogin::test_login_success` | `/api/auth/login` | POST | 正确账号 → 200 + access_token + role |
| 6 | `TestAuthLogin::test_login_wrong_password` | `/api/auth/login` | POST | 密码错误 → **401** |
| 7 | `TestAuthLogin::test_login_nonexistent_user` | `/api/auth/login` | POST | 用户不存在 → **401**（不枚举） |
| 8 | `TestAuthMe::test_me_returns_current_user` | `/api/auth/me` | GET | 有效 token → 200 + 用户信息 |
| 9 | `TestAuthMe::test_me_no_token_401` | `/api/auth/me` | GET | 无 Authorization 头 → **401** |
| 10 | `TestAuthMe::test_me_invalid_token_401` | `/api/auth/me` | GET | 伪造 token → **401** |

#### Contracts 路由

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 11 | `TestContracts::test_upload_txt_and_list` | `/api/contracts/upload` + 列表 + 详情 | POST / GET | TXT 上传后列表可见、详情能读回正文 |
| 12 | `TestContracts::test_upload_unsupported_extension` | `/api/contracts/upload` | POST | .exe 文件 → **400** |
| 13 | `TestContracts::test_upload_empty_content` | `/api/contracts/upload` | POST | 文件只有空白 → **400** |
| 14 | `TestContracts::test_get_nonexistent_contract` | `/api/contracts/99999` | GET | 不存在的 id → **404** |
| 15 | `TestContracts::test_upload_new_version` | `/api/contracts/{id}/versions` | POST | v1 → v2，version_no 自增到 2 |
| 16 | `TestContracts::test_unauthorized_access` | `/api/contracts` | GET | 无 token → **401** |

#### Knowledge 路由（Clause + Regulation）

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 17 | `TestKnowledgeClauses::test_admin_crud_clause` | `/api/knowledge/clauses` | CRUD | admin 全链路：创建 → 列表 → 更新 → 删除 |
| 18 | `TestKnowledgeClauses::test_normal_user_cannot_write_clause` | `/api/knowledge/clauses` | POST | 普通用户写 → **403** |
| 19 | `TestKnowledgeClauses::test_update_nonexistent_clause` | `/api/knowledge/clauses/99999` | PUT | 不存在 → **404** |
| 20 | `TestKnowledgeClauses::test_delete_nonexistent_clause` | `/api/knowledge/clauses/99999` | DELETE | 不存在 → **404** |
| 21 | `TestKnowledgeRegulations::test_admin_crud_regulation` | `/api/knowledge/regulations` | CRUD | admin 创建 → 列表 → 删除 |
| 22 | `TestKnowledgeRegulations::test_normal_user_cannot_write_regulation` | `/api/knowledge/regulations` | POST | 普通用户写 → **403** |

#### Rebuild Index

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 23 | `TestRebuildIndex::test_rebuild_empty_knowledge_400` | `/api/knowledge/rebuild-index` | POST | 知识库空 → **400** |
| 24 | `TestRebuildIndex::test_rebuild_with_data` | `/api/knowledge/rebuild-index` | POST | 有数据 → 200，`indexed=1` |
| 25 | `TestRebuildIndex::test_rebuild_requires_admin` | `/api/knowledge/rebuild-index` | POST | 普通用户 → **403** |

#### Compare 路由

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 26 | `TestCompare::test_compare_texts_success` | `/api/compare/text` | POST | 正常比对 → 200，返回 summary+diffs |
| 27 | `TestCompare::test_compare_texts_empty_input` | `/api/compare/text` | POST | 空文本 → **400** |
| 28 | `TestCompare::test_compare_texts_unauthorized` | `/api/compare/text` | POST | 无 token → **401** |
| 29 | `TestCompare::test_compare_versions_not_found` | `/api/compare/versions` | POST | 合同不存在 → **404** |

#### Root

| # | 用例 | 端点 | HTTP | 说明 |
|---|------|------|------|------|
| 30 | `test_root_endpoint` | `/` | GET | 健康检查 → 200，返回 app 名称和 docs 路径 |

---

## 四、HTTP 状态码覆盖矩阵

| 状态码 | 覆盖端点数 | 典型场景 |
|--------|-----------|---------|
| **200 OK** | 19 | 成功注册 / 登录 / 获取用户 / 上传合同 / CRUD / 比对 / 健康检查 |
| **400 Bad Request** | 4 | 参数校验失败（用户名过短、密码过短、非法扩展名、空知识库 rebuild） |
| **401 Unauthorized** | 5 | 无 token、伪造 token、密码错误、用户不存在 |
| **403 Forbidden** | 3 | 普通用户尝试写知识库、普通用户调 rebuild-index |
| **404 Not Found** | 3 | 合同不存在、条款不存在、法规不存在、比对合同不存在 |

---

## 五、测试文件结构

```
backend/
├── tests/
│   ├── __init__.py                 # 空包标记
│   ├── conftest.py                 # pytest fixtures（全局共享）
│   ├── test_security.py            # 11 条 — 密码哈希 + JWT
│   ├── test_splitter.py            #  7 条 — 合同条款切分
│   ├── test_document_parser.py     #  4 条 — TXT/DOCX 解析
│   ├── test_vector_store.py        #  5 条 — NumPy 降级向量检索
│   ├── test_compare_service.py     #  9 条 — 条款比对逻辑
│   └── test_api.py                 # 30 条 — FastAPI 端到端接口
├── app/                            # 被测源码
│   ├── core/                       # config.py / database.py / security.py
│   ├── rag/                        # splitter.py / vector_store.py / embedder.py
│   ├── services/                   # document_parser.py / compare_service.py
│   └── api/routes/                 # auth.py / contracts.py / knowledge.py / compare.py
```

---

## 六、如何运行

### 依赖安装

```bash
pip install pytest httpx
# 生产依赖已在上一轮安装过，只需补这两个
```

### 常用命令

```bash
# 全量测试（简洁模式）
cd backend && python3 -m pytest tests/ -q

# 全量测试（详细输出）
cd backend && python3 -m pytest tests/ -v

# 只跑某个文件
python3 -m pytest tests/test_api.py -v

# 只跑某个类/某个函数
python3 -m pytest tests/test_api.py::TestAuthLogin -v
python3 -m pytest tests/ -k "register"           # 按关键字过滤

# 生成覆盖率报告（需额外 pip install pytest-cov）
python3 -m pytest tests/ --cov=app --cov-report=term-missing
```

---

## 七、已知限制

| 限制 | 说明 | 缓解措施 |
|------|------|---------|
| review / generation / chat / compliance 路由未测 | 内部调用 LLM，用户明确不测模型相关 | 如后续需覆盖，可用 `unittest.mock.patch` mock `get_llm()` 返回一个 mock 对象 |
| 向量检索走 NumPy 降级路径 | macOS + Python 3.13 装不上 faiss-cpu 和 sentence-transformers | 降级路径足以验证业务逻辑，语义精度略低但分类判断有效 |
| Pydantic / SQLAlchemy 弃用警告 | 用了 `class Config` 和 `datetime.utcnow()` | 与测试无关，后续源码升级时统一修复 |
| 未测 PDF 解析 | PyMuPDF 依赖可用，但生成真实 PDF 较复杂 | 如需覆盖可临时跳过，TXT + DOCX 已验证 `parse_document` 主逻辑 |
