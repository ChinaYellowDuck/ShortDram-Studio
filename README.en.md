# ShortDram Studio — AI Multi-Agent Short Drama Production Platform

> 🎬 From idea to final cut — an all-in-one AI short drama generation solution powered by multi-agent collaboration

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-developing-yellow.svg)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)
![LangGraph](https://img.shields.io/badge/🦜🕸️-LangGraph-black)
![LangChain](https://img.shields.io/badge/🦜🔗-LangChain-green)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?logo=fastapi)
![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs)

[简体中文](README.md) | English

ShortDram Studio is an open-source **AI multi-agent driven** short drama production platform built on LangGraph. It enables anyone to easily create high-quality short drama content. By orchestrating specialized agents — screenwriter, character designer, storyboard artist, voice director, and video editor — the platform covers the entire production pipeline from **ideation → screenplay → character design → storyboarding → AI voiceover → video compositing**.

---

## ✨ Key Features

### 🤖 Multi-Agent Collaboration Architecture
- **Screenwriter Agent**: Professional script generation across genres, with three-act structure and plot twist optimization
- **Character Designer Agent**: Character profile generation + visual artwork with consistency across scenes
- **Storyboard Artist Agent**: Automatically breaks scripts into storyboards with cinematic language and shot descriptions
- **Voice Director Agent**: One-stop line allocation, voice casting, and emotion scheduling
- **Video Editor Agent**: Orchestrates image generation, subtitles, BGM, and transitions to produce the final cut
- **Producer Agent**: Global coordination + quality control, ensuring all outputs meet production standards

### 📝 Intelligent Screenplay Generation
- Generate complete short drama scripts from a single prompt (urban, xianxia, romance, thriller, and more)
- LLM-powered script structure optimization with automatic plot twists and payoff moments
- Iterative dialogue-based script refinement, with chapter/scene-level granular edits
- Export to Word, PDF, plain text, and more

### 🎨 Character & Scene Design
- Auto-generated character profile cards (appearance, personality, costumes, backstory)
- AI character visual generation with multiple style options (realistic, anime, guofeng, etc.)
- Scene concept art generated in sync with script scenes
- Asset library for characters and scenes, reusable across projects

### 🎙️ AI Voiceover & Sound Design
- Multi-character speech synthesis with varied timbre, emotion, and pacing
- Automatic line allocation with intelligent voice matching per character
- Auto-recommended sound effects and BGM matched to scene mood
- Custom voice cloning support (requires compatible TTS service)

### 🎥 Automated Video Compositing
- Shot-level video clip generation (text-to-image + motion / text-to-video)
- Automatic subtitle generation with customizable styling
- Smart transition effects matched to scene emotion
- One-click export in vertical / horizontal formats

### 🛠️ Project Management & Observability
- Manage multiple projects in parallel with clear progress tracking
- Full agent runtime tracing via LangSmith — every decision is auditable
- Version history with rollback support
- Team collaboration (planned)
- Template marketplace for popular short drama formats

---

## 🏗️ Architecture

### Frontend
- **Framework**: Vue 3 + TypeScript (Composition API)
- **Build Tool**: Vite
- **UI Library**: Element Plus / Naive UI
- **State Management**: Pinia
- **Router**: Vue Router 4
- **Video Player**: Video.js / Plyr

### Backend & AI Agents
- **Web Framework**: FastAPI
- **AI Framework**: LangChain 1.x + LangGraph
- **Observability**: LangSmith (agent tracing, evaluation, debugging)
- **Database**: PostgreSQL + Redis
- **File Storage**: Local / S3-compatible object storage
- **Task Queue**: Celery + Redis / Arq
- **Video Processing**: FFmpeg

### Multi-Agent Architecture

```
                        ┌─────────────────┐
                        │  Producer Agent │  ← Global coord. + QA
                        └────────┬────────┘
                                 │
        ┌────────────┬───────────┼───────────┬────────────┐
        ▼            ▼           ▼           ▼            ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
   │ Screen- │ │Character│ │Story-   │ │ Voice   │ │  Video   │
   │ writer  │ │Designer │ │board    │ │Director │ │  Editor  │
   │  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │ │  Agent   │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └──────────┘
```

Agent capabilities:
- **Stateful execution**: LangGraph state graph with checkpoint resume
- **Human-in-the-loop**: Human review and intervention at key nodes
- **Tool calling**: Each agent can call image gen, TTS, video synthesis, and other tools
- **Memory system**: Project-level shared memory + agent private memory
- **Observability**: Full-stack LangSmith tracing, every decision is auditable

### AI Model Support
| Capability | Supported Models / Services |
|------------|------------------------------|
| Text (LLM) | Claude, GPT-4o, ERNIE, Qwen, DeepSeek |
| Image Generation | Stable Diffusion, DALL·E 3, Jimeng, Kling |
| Speech (TTS) | Azure TTS, iFlytek, Aliyun TTS, Edge TTS, ElevenLabs |
| Video Generation | Sora, Runway, Kling, Jimeng Video, Pika |
| Embedding | text-embedding, bge-m3 |

---

## 🚀 Getting Started

### Prerequisites
- Node.js >= 18.x
- Python >= 3.11
- PostgreSQL >= 14
- Redis >= 7
- FFmpeg (required for video compositing)
- LangSmith API Key (optional, for agent tracing)

### Local Development

```bash
# Clone the repo
git clone https://github.com/your-username/ShortDram-Studio.git
cd ShortDram-Studio

# Install frontend dependencies
cd frontend
npm install
npm run dev

# Install backend dependencies (new terminal)
cd ../backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your LLM API keys, database connection, etc.

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

### Docker Deployment

```bash
# One-click startup with docker-compose
docker-compose up -d
```

Visit `http://localhost:5173` for the frontend, and `http://localhost:8000/docs` for the API docs.

### LangSmith Setup (Optional)

Enable LangSmith to trace all agent runs, token usage, error logs, and more:

```bash
# Set in .env
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=your-api-key
export LANGCHAIN_PROJECT=shortdram-studio
```

---

## 📁 Project Structure

```
ShortDram-Studio/
├── frontend/                    # Vue 3 frontend
│   ├── src/
│   │   ├── components/          # Shared components
│   │   ├── views/               # Page views
│   │   ├── stores/              # Pinia state management
│   │   ├── router/              # Router config
│   │   ├── api/                 # API request wrappers
│   │   └── utils/               # Utilities
│   └── package.json
├── backend/                     # FastAPI + LangGraph backend
│   ├── app/
│   │   ├── agents/              # Agent definitions
│   │   │   ├── screenwriter/    # Screenwriter agent
│   │   │   ├── character_designer/  # Character designer agent
│   │   │   ├── storyboarder/    # Storyboard artist agent
│   │   │   ├── voice_director/  # Voice director agent
│   │   │   ├── video_editor/    # Video editor agent
│   │   │   └── producer/        # Producer coordinator agent
│   │   ├── graphs/              # LangGraph state graph definitions
│   │   ├── tools/               # Agent toolset
│   │   ├── services/            # Business service layer
│   │   ├── models/              # Data models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/                 # API routes
│   │   └── main.py              # App entry point
│   ├── tests/                   # Tests
│   ├── requirements.txt
│   └── .env.example
├── docker/                      # Docker config
├── docs/                        # Documentation
├── .github/                     # GitHub Actions workflows
├── LICENSE                      # MIT License
├── README.md                    # Chinese readme
└── README.en.md                 # English readme
```

---

## 🗺️ Roadmap

- [ ] **v0.1** — Agent Framework + Script Generation
  - [ ] LangGraph multi-agent foundation
  - [ ] Screenwriter agent (script generation + iterative refinement)
  - [ ] Producer coordinator agent (workflow orchestration)
  - [ ] Script editor (scene splitting + rich text)
  - [ ] Basic project management
  - [ ] LangSmith observability integration

- [ ] **v0.2** — Character Design + Storyboard Agent
  - [ ] Character designer agent (profile + visual generation)
  - [ ] Storyboard artist agent (script → storyboard)
  - [ ] Scene concept art generation
  - [ ] Asset library
  - [ ] Human review nodes (human-in-the-loop)

- [ ] **v0.3** — Voice Director Agent
  - [ ] Voice director agent (line allocation + voice casting)
  - [ ] Multi-character TTS integration
  - [ ] Auto-matched sound effects and BGM
  - [ ] Voice preview and fine-tuning

- [ ] **v0.4** — Video Editor Agent
  - [ ] Video editor agent (end-to-end pipeline)
  - [ ] Storyboard video / image generation
  - [ ] Automatic subtitle generation
  - [ ] One-click export (vertical / horizontal)

- [ ] **v1.0** — Full Pipeline + Template Marketplace
  - [ ] End-to-end fully automated pipeline
  - [ ] Short drama template marketplace
  - [ ] Quality evaluation agent (auto-scoring)
  - [ ] Team collaboration
  - [ ] Plugin system (extend agent capabilities)

---

## 🤝 Contributing

We welcome contributions of all kinds — bug reports, feature requests, documentation improvements, and code contributions. Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

### Quick Start
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 💬 Community & Support

- 📖 [Documentation](docs/)
- 💡 [Report an Issue](https://github.com/your-username/ShortDram-Studio/issues)
- 💬 Discussion group (WeChat / Telegram, coming soon)

---

## 📄 License

This project is open source under the [MIT License](LICENSE). You are free to use, modify, and distribute it.

---

## ⭐ Show Your Support

If this project helps you, please consider:

- Starring the repository ⭐
- Sharing it with others who might benefit
- Submitting issues and PRs to help improve it

---

> **Note**: This project is under active development. Features and APIs are subject to change. Please wait for the v1.0 release for production use.
