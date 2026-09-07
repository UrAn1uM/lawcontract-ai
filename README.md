# 智能法律合同审查与生成系统

面向企业合同管理与法律合规审查场景，基于 LangChain 构建"RAG + Agent"双链路架构的智能法律系统。

## 功能

| 模块 | 说明 |
|---|---|
| 合同智能审查 | 上传合同逐条审查，识别法律风险/权利义务不对等条款，输出修改建议与依据 |
| 标准合同生成 | 问答式填写合同要素，LLM 起草标准合同 + 规则自检必备条款 |
| 条款库与比对 | 标准条款库维护；两份合同/新旧版本的条款级 diff + 语义比对 |
| 合规性检查 | 依据 GDPR、《数据安全法》《个人信息保护法》检查条款合规性 |
| 智能问答 | Agent 自主决定检索条款库/法规库，回答合同法律问题 |
| 知识库管理后台 | 条款/法规 CRUD + 向量索引一键重建 |

## 技术栈

- 后端：Python 3.10+ / FastAPI / SQLAlchemy / MySQL（开发默认 SQLite）
- AI：LangChain（RAG 检索链 + tool-calling Agent）/ DeepSeek（OpenAI 兼容协议）/ 向量默认轻量哈希（可选 BGE 语义模型）
- 检索：BM25（jieba）+ 向量召回（FAISS，装不上自动降级 NumPy）+ RRF 融合
- 前端：Vue 3 / Vite / Element Plus / Pinia
- 部署：Docker Compose（MySQL + 后端）

## 目录结构

```
law-contract-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # 应用入口
│   │   ├── models.py            # ORM 实体
│   │   ├── core/                # 配置 / 数据库 / JWT 安全
│   │   ├── api/routes/          # 8 组路由
│   │   ├── services/            # 审查/生成/比对/问答业务逻辑
│   │   ├── agents/              # LangChain Agent 与工具
│   │   ├── rag/                  # 切分/向量库/混合检索/入库
│   │   └── prompts/             # 审查清单/合规/生成 Prompt
│   ├── scripts/                 # seed_data 种子数据 / rebuild_index 重建索引
│   └── requirements.txt
├── frontend/
│   └── src/views/               # 登录/审查/生成/比对/问答/知识库
└── docker-compose.yml
```

## 快速启动（本地开发）

### 1. 后端

```bash
cd backend

# 创建虚拟环境并安装依赖（Windows）
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量：复制 .env.example 为 .env，填入 DeepSeek API Key
# 申请地址 https://platform.deepseek.com

# 启动（默认 SQLite，零配置）
uvicorn app.main:app --reload --port 8000
```

接口文档自动生成：http://localhost:8000/docs

### 2. 初始化知识库（首次必做）

```bash
# 导入 10 条标准条款 + 9 条法规种子数据
python -m scripts.seed_data

# 构建向量索引（默认用轻量哈希向量，无需下载模型；如已安装 sentence-transformers 则自动用语义向量）
python -m scripts.rebuild_index
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

### 4. 默认账号

| 账号 | 密码 | 角色 |
|---|---|---|
| admin | admin123 | 管理员（可管理知识库） |
| demo | demo123 | 普通用户 |

## Docker 部署（MySQL + 后端）

```bash
# 在 law-contract-ai 目录下
export LLM_API_KEY=sk-xxxx      # Windows CMD: set LLM_API_KEY=sk-xxxx
docker compose up -d
```

后端：http://localhost:8000，MySQL 端口 3306，密码 root123。前端仍本地 `npm run dev` 或自行构建静态部署。

## 核心链路（面试讲解用）

```
合同上传 -> 解析(docx/pdf) -> 按"第X条"切分
    -> 逐条混合检索(BM25+向量, RRF融合) 召回标准条款/法规
    -> LLM 按审查清单 Prompt 分析 -> 结构化 JSON 报告(等级/建议/依据)
```

防幻觉三重约束：检索不到依据不输出 / legal_basis 必须引用来源 / JSON 解析失败降级为空。

## 常见问题

| 问题 | 处理 |
|---|---|
| faiss-cpu 安装失败 | 无需处理，代码自动降级 NumPy 检索（数据量大时再解决） |
| 首次检索/比对很慢 | 已用轻量哈希向量，首次运行只需加载 jieba 分词（约 1 秒），不再下载模型 |
| 审查报错"未配置 LLM_API_KEY" | backend 目录下复制 .env.example 为 .env 并填 Key |
| 想升级语义检索精度 | `pip install sentence-transformers`（会拉 torch 约 2.5GB）后 `python -m scripts.rebuild_index` 重建索引 |
| 知识库改了没生效 | 知识库管理页点"重建向量索引" |

## 免责声明

本系统输出仅辅助初审，种子法规数据为教学节选，不能替代执业律师意见。
