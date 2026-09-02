# ShortDram Studio Backend

基于 FastAPI + LangGraph 的 AI 多智能体短剧制作平台后端。

## 技术栈

- **Web 框架**: FastAPI
- **AI 框架**: LangChain 1.x + LangGraph
- **可观测性**: LangSmith (可选)
- **数据库**: SQLite (开发) / PostgreSQL (生产) + SQLAlchemy 2.x + Alembic
- **数据校验**: Pydantic v2

## 快速开始

### 1. 安装依赖

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，配置数据库、加密密钥等
```

生成加密密钥（用于加密 LLM API Key）：

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. 初始化数据库

```bash
alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 项目结构

```
backend/
├── app/
│   ├── api/               # API 路由层
│   ├── agents/            # 智能体模块
│   ├── graphs/            # 多智能体协同图
│   ├── models/            # SQLAlchemy 数据模型
│   ├── schemas/           # Pydantic Schema
│   ├── services/          # 业务服务层
│   ├── tools/             # 智能体工具集
│   ├── utils/             # 工具函数
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── dependencies.py    # 依赖注入
│   └── main.py            # 应用入口
├── alembic/               # 数据库迁移
├── tests/                 # 测试
└── requirements.txt
```

## 核心模块

### LLM 配置管理

支持多 LLM 配置保存、设默认、使用时切换：

- API: `GET/POST/PUT/DELETE /api/v1/llm-configs`
- 支持的 Provider: openai, anthropic, deepseek, qwen, zhipu, ollama
- API Key 使用 Fernet 加密存储

### 智能体模块

每个智能体为独立模块，包含：
- `agent.py` — 智能体业务封装
- `graph.py` — LangGraph 状态图定义

通过 LLM 工厂类根据配置 ID 动态实例化模型。

## 测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=app --cov-report=html
```

## 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚上一个迁移
alembic downgrade -1
```

## LangSmith 集成

在 `.env` 中设置：

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-api-key
LANGCHAIN_PROJECT=shortdram-studio
```

开启后所有智能体运行都会自动追踪到 LangSmith 平台。
