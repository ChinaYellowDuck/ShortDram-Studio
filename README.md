# ShortDram Studio — AI 智能体全流程短剧制作平台

> 🎬 从创意到成片，多智能体协同的一站式 AI 短剧生成解决方案

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-developing-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![LangGraph](https://img.shields.io/badge/🦜🕸️-LangGraph-black)
![LangChain](https://img.shields.io/badge/🦜🔗-LangChain-green)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs)

ShortDram Studio 是一款开源的 **AI 多智能体驱动**全流程短剧制作平台，基于 LangGraph 构建多智能体协作工作流，致力于让每个人都能轻松创作高质量的短剧内容。通过编排编剧、角色设计、分镜师、配音导演等多个专业智能体协同工作，平台覆盖从**创意构思 → 剧本创作 → 角色设定 → 分镜设计 → AI 配音 → 视频合成**的完整制作链路。

---

## ✨ 核心特性

### 🤖 多智能体协作架构
- **编剧智能体**: 专业剧本创作，支持多题材、多风格，自带三幕式/起承转合结构把控
- **角色设计智能体**: 角色人设生成 + 形象图绘制，保持角色一致性
- **分镜师智能体**: 自动拆解剧本为分镜脚本，匹配镜头语言和画面描述
- **配音导演智能体**: 台词分配、音色选择、情绪调度一站式完成
- **视频合成智能体**: 统筹画面生成、字幕、BGM、转场，输出最终成片
- **制片人智能体**: 全局协调 + 质量把控，确保各环节输出符合短剧制作规范

### 📝 智能剧本创作
- 支持一句话生成完整短剧剧本（都市、仙侠、甜宠、悬疑等多种题材）
- 基于大模型的剧本结构优化，自动制造爽点和反转
- 多轮对话式剧本打磨，支持章节/场景级别的精细修改
- 剧本导出：支持 Word、PDF、纯文本等多种格式

### 🎨 角色与场景设计
- 角色人设卡片自动生成（外貌、性格、服装、背景故事）
- AI 角色形象图生成，支持风格化调整（写实、二次元、国风等）
- 场景概念图自动生成，与剧本场景一一对应
- 角色/场景资产管理库，支持跨项目复用

### 🎙️ AI 配音与音效
- 多角色语音合成，支持不同音色、情绪、语速
- 自动台词分配，按角色智能匹配音色
- 背景音效与 BGM 自动推荐与匹配
- 支持自定义音色克隆（需接入对应服务）

### 🎥 视频自动合成
- 分镜级视频片段自动生成（文生图 + 动态化 / 文生视频）
- 字幕自动生成与样式定制
- 转场效果智能匹配场景情绪
- 一键导出竖屏/横屏多种规格

### 🛠️ 项目管理与可观测性
- 多项目并行管理，进度一目了然
- 基于 LangSmith 的完整智能体运行追踪，每一步决策可回溯
- 版本历史记录，支持随时回退
- 团队协作支持（规划中）
- 模板市场，一键套用热门短剧模板

---

## 🏗️ 技术架构

### 前端
- **框架**: Vue 3 + TypeScript (Composition API)
- **构建工具**: Vite
- **UI 组件库**: Element Plus / Naive UI
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **视频预览**: Video.js / Plyr

### 后端与 AI 智能体
- **Web 框架**: FastAPI
- **AI 框架**: LangChain 1.x + LangGraph
- **可观测性**: LangSmith（智能体运行追踪、评估、调试）
- **数据库**: PostgreSQL + Redis
- **文件存储**: 本地 / S3 兼容对象存储
- **任务队列**: Celery + Redis / Arq
- **视频处理**: FFmpeg

### 多智能体架构

```
                        ┌─────────────────┐
                        │  制片人智能体   │  ← 全局协调 + 质量审核
                        └────────┬────────┘
                                 │
        ┌────────────┬───────────┼───────────┬────────────┐
        ▼            ▼           ▼           ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
   │ 编剧    │ │ 角色    │ │ 分镜师  │ │ 配音    │ │ 视频合成 │
   │ 智能体  │ │ 设计    │ │ 智能体  │ │ 导演    │ │ 智能体   │
   │         │ │ 智能体  │ │         │ │ 智能体  │ │          │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘
```

智能体特性：
- **有状态执行**: 基于 LangGraph 的状态图，支持断点续跑
- **人机协作**: 关键节点支持人工介入和审核
- **工具调用**: 每个智能体可调用图像生成、TTS、视频合成等工具
- **记忆系统**: 项目级共享记忆 + 智能体私有记忆
- **可观测性**: 全链路 LangSmith 追踪，每一步决策可审计

### AI 模型适配
| 能力 | 支持的模型/服务 |
|------|----------------|
| 文本生成（LLM） | Claude, GPT-4o, 文心一言, 通义千问, DeepSeek |
| 图像生成 | Stable Diffusion, DALL·E 3, 即梦, 可灵 |
| 语音合成（TTS） | Azure TTS, 讯飞, 阿里云 TTS, Edge TTS, ElevenLabs |
| 视频生成 | Sora, Runway, 可灵, 即梦视频, Pika |
| Embedding | text-embedding, bge-m3 |

---

## 🚀 快速开始

### 环境要求
- Node.js >= 18.x
- Python >= 3.11
- PostgreSQL >= 14
- Redis >= 7
- FFmpeg（视频合成必需）
- LangSmith API Key（可选，用于智能体追踪）

### 本地开发

```bash
# 克隆项目
git clone https://github.com/your-username/ShortDram-Studio.git
cd ShortDram-Studio

# 安装前端依赖
cd frontend
npm install
npm run dev

# 安装后端依赖（新开终端）
cd ../backend
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM API Key、数据库连接等配置

# 启动后端服务
uvicorn app.main:app --reload --port 8000
```

### Docker 部署

```bash
# 使用 docker-compose 一键启动
docker-compose up -d
```

访问 `http://localhost:5173` 即可使用前端，后端 API 文档在 `http://localhost:8000/docs`。

### LangSmith 配置（可选）

开启 LangSmith 可追踪所有智能体的运行过程、token 消耗、错误日志等：

```bash
# 在 .env 中设置
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your-api-key
export LANGCHAIN_PROJECT=shortdram-studio
```

---

## 📁 项目结构

```
ShortDram-Studio/
├── frontend/                    # Vue 3 前端应用
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   ├── views/               # 页面视图
│   │   ├── stores/              # Pinia 状态管理
│   │   ├── router/              # 路由配置
│   │   ├── api/                 # API 请求封装
│   │   └── utils/               # 工具函数
│   └── package.json
├── backend/                     # FastAPI + LangGraph 后端
│   ├── app/
│   │   ├── agents/              # 智能体定义
│   │   │   ├── screenwriter/    # 编剧智能体
│   │   │   ├── character_designer/  # 角色设计智能体
│   │   │   ├── storyboarder/    # 分镜师智能体
│   │   │   ├── voice_director/  # 配音导演智能体
│   │   │   ├── video_editor/    # 视频合成智能体
│   │   │   └── producer/        # 制片人协调智能体
│   │   ├── graphs/              # LangGraph 状态图定义
│   │   ├── tools/               # 智能体工具集
│   │   ├── services/            # 业务服务层
│   │   ├── models/              # 数据模型
│   │   ├── schemas/             # Pydantic 模式
│   │   ├── api/                 # API 路由
│   │   └── main.py              # 应用入口
│   ├── tests/                   # 测试
│   ├── requirements.txt
│   └── .env.example
├── docker/                      # Docker 相关配置
├── docs/                        # 项目文档
├── .github/                     # GitHub Actions 工作流
├── LICENSE                      # MIT 许可证
└── README.md
```

---

## 🗺️ 路线图

- [ ] **v0.1** — 智能体框架 + 剧本生成
  - [ ] LangGraph 多智能体基础框架搭建
  - [ ] 编剧智能体（剧本生成 + 多轮打磨）
  - [ ] 制片人协调智能体（流程编排）
  - [ ] 剧本编辑器（场景分割 + 富文本）
  - [ ] 项目管理基础功能
  - [ ] LangSmith 可观测性接入

- [ ] **v0.2** — 角色设计 + 分镜智能体
  - [ ] 角色设计智能体（人设 + 形象图生成）
  - [ ] 分镜师智能体（剧本转分镜脚本）
  - [ ] 场景概念图生成
  - [ ] 资产管理库
  - [ ] 人工审核节点（人机协作）

- [ ] **v0.3** — 配音导演智能体
  - [ ] 配音导演智能体（台词分配 + 音色匹配）
  - [ ] 多角色语音合成接入
  - [ ] 音效与 BGM 自动匹配
  - [ ] 语音预览与微调

- [ ] **v0.4** — 视频合成智能体
  - [ ] 视频合成智能体（全流程串接）
  - [ ] 分镜视频/图片生成
  - [ ] 字幕自动生成
  - [ ] 一键导出竖屏/横屏

- [ ] **v1.0** — 全流程打通 + 模板市场
  - [ ] 端到端全自动化 Pipeline
  - [ ] 短剧模板市场
  - [ ] 质量评估智能体（自动评分）
  - [ ] 团队协作功能
  - [ ] 插件系统（扩展智能体能力）

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！无论是提交 Bug、提出新功能、完善文档还是提交代码，请阅读 [CONTRIBUTING.md](docs/CONTRIBUTING.md) 了解详情。

### 快速参与
1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

---

## 💬 社区与支持

- 📖 [文档中心](docs/)
- 💡 [提交 Issue](https://github.com/your-username/ShortDram-Studio/issues)
- 💬 讨论群（微信/Telegram，待开通）

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源，你可以自由地使用、修改和分发。

---

## ⭐ 支持我们

如果你觉得这个项目对你有帮助，欢迎：

- 给项目点个 Star ⭐
- 分享给更多有需要的人
- 提交 Issue 和 PR 参与贡献

---

> **注意**: 本项目正在积极开发中，功能和 API 可能会发生变化。生产环境使用请等待 v1.0 正式发布。
