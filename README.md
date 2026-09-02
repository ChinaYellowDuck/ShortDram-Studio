# ShortDram Studio — AI 全流程短剧制作平台

> 🎬 从创意到成片，一站式 AI 短剧生成解决方案

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-developing-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

ShortDram Studio 是一款开源的 AI 驱动全流程短剧制作平台，致力于让每个人都能轻松创作高质量的短剧内容。通过集成大语言模型、图像生成、语音合成和视频合成技术，平台覆盖从**剧本创作 → 分镜设计 → 角色设定 → AI 配音 → 视频合成**的完整制作链路。

---

## ✨ 核心特性

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

### 🛠️ 项目管理
- 多项目并行管理，进度一目了然
- 版本历史记录，支持随时回退
- 团队协作支持（规划中）
- 模板市场，一键套用热门短剧模板

---

## 🏗️ 技术架构

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 组件库**: Ant Design / shadcn-ui
- **状态管理**: Zustand
- **视频预览**: Video.js / Plyr

### 后端
- **框架**: Node.js (NestJS) / Python (FastAPI) — 双后端架构
- **数据库**: PostgreSQL + Redis
- **文件存储**: 本地 / S3 兼容对象存储
- **消息队列**: BullMQ (Redis)
- **AI 接入层**: 统一适配层，支持多模型厂商切换

### AI 模型适配
| 能力 | 支持的模型/服务 |
|------|----------------|
| 文本生成 | Claude, GPT-4, 文心一言, 通义千问, DeepSeek |
| 图像生成 | Stable Diffusion, Midjourney API, DALL·E, 即梦 |
| 语音合成 | Azure TTS, 讯飞, 阿里云 TTS, Edge TTS |
| 视频生成 | Sora, Runway, 可灵, 即梦视频 |

---

## 🚀 快速开始

### 环境要求
- Node.js >= 18.x
- Python >= 3.10
- PostgreSQL >= 14
- Redis >= 7
- FFmpeg（视频合成必需）

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
cd backend
npm install
npm run start:dev

# 安装 AI 服务依赖（新开终端）
cd ai-service
pip install -r requirements.txt
python main.py
```

### Docker 部署

```bash
# 使用 docker-compose 一键启动
docker-compose up -d
```

访问 `http://localhost:3000` 即可使用。

---

## 📁 项目结构

```
ShortDram-Studio/
├── frontend/              # 前端 Web 应用
│   ├── src/
│   │   ├── components/    # 通用组件
│   │   ├── pages/         # 页面模块
│   │   ├── stores/        # 状态管理
│   │   └── utils/         # 工具函数
│   └── package.json
├── backend/               # 业务后端（NestJS）
│   ├── src/
│   │   ├── modules/       # 业务模块
│   │   ├── common/        # 公共组件
│   │   └── main.ts
│   └── package.json
├── ai-service/            # AI 服务（Python/FastAPI）
│   ├── services/          # AI 模型适配
│   ├── pipelines/         # 处理流水线
│   └── main.py
├── docker/                # Docker 相关配置
├── docs/                  # 项目文档
├── .github/               # GitHub Actions 工作流
├── LICENSE                # MIT 许可证
└── README.md
```

---

## 🗺️ 路线图

- [ ] **v0.1** — 剧本生成核心功能
  - [ ] 基于大模型的短剧剧本生成
  - [ ] 剧本编辑器（富文本 + 场景分割）
  - [ ] 项目管理基础功能

- [ ] **v0.2** — 角色与场景设计
  - [ ] AI 角色形象生成
  - [ ] 场景概念图生成
  - [ ] 资产管理库

- [ ] **v0.3** — AI 配音
  - [ ] 多角色语音合成
  - [ ] 台词自动分配
  - [ ] 音效与 BGM 匹配

- [ ] **v0.4** — 视频合成
  - [ ] 分镜视频生成
  - [ ] 字幕自动生成
  - [ ] 一键导出

- [ ] **v1.0** — 全流程打通 + 模板市场
  - [ ] 全流程自动化 Pipeline
  - [ ] 短剧模板市场
  - [ ] 团队协作功能

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
