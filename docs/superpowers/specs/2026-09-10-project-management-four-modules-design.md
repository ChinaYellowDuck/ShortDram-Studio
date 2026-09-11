# 项目管理四大模块设计文档

> 日期：2026-09-10
> 状态：设计确认
> 范围：项目管理整体架构重构，涵盖剧本管理、资产管理、分镜管理、视频合成四大模块

## 1. 背景与目标

当前 ShortDram Studio 已有基础的 Project 和 Script 数据模型，但缺乏完整的短剧制作流水线支撑。项目需要从简单的"项目+剧本"结构，演进为覆盖从创意到成片全流程的完整制作平台。

**目标：** 构建四大模块（剧本管理、资产管理、分镜管理、视频合成）的线性流水线，每个模块的产出是下一个模块的输入，形成清晰、可控的短剧制作工作流。

## 2. 整体架构

### 2.1 四大模块

```
剧本管理 → 资产管理 → 分镜管理 → 视频合成 → 完成
  (Script)   (Asset)   (Storyboard)   (Video)
```

每个模块对应项目的一个阶段，采用线性阶段制：必须完成当前阶段并确认后，才能进入下一阶段。支持解锁回退。

### 2.2 项目阶段（ProjectPhase）

| 阶段 | 枚举值 | 描述 |
|------|--------|------|
| 剧本阶段 | `script` | 创建/导入剧本，确认剧本内容 |
| 资产阶段 | `asset` | 提取并确认所有人物、场景、道具资产 |
| 分镜阶段 | `storyboard` | 生成并确认场景级分镜 |
| 视频阶段 | `video` | 生成视频片段、配音，合成最终视频 |
| 完成 | `completed` | 项目完成，成片已导出 |

替代原有的 `ProjectStatus`（draft/in_progress/completed/archived），新增 `phase` 字段表示当前阶段，`status` 保留用于表示项目的运行态（active/archived）。

## 3. 模块详细设计

### 3.1 剧本管理（Script）

**核心能力：** 小说导入 → 大纲确认 → 剧本生成，分步引导式创作。

**数据模型（已有，需扩展）：**
- `Script` — 剧本主表（已存在）
- `ScriptScene` — 剧本场景（已存在）
- `ScriptCharacter` — 剧本角色（已存在）
- `ScriptDialogue` — 台词（已存在）

**新增字段：**
- `Script.source_type` — 剧本来源：`novel` / `ai_generated` / `manual`
- `Script.source_text` — 原始小说文本（当 source_type=novel 时）
- `Script.outline` — 故事大纲（JSON 或 Text，分步引导的中间产物）
- `Script.episode_index` — 当前第几集（多集剧本）

**核心功能：**
1. 小说文本上传（支持 .txt / .docx）
2. AI 生成故事大纲（可修改、可重生成）
3. AI 生成人物小传（可增删改）
4. AI 逐集生成剧本（分步确认，每集生成后用户确认再生成下一集）
5. 剧本可视化编辑器（场景列表 + 台词编辑）
6. 剧本版本历史

**API 接口（新增）：**
- `POST /api/v1/projects/{id}/script/import-novel` — 上传小说并启动大纲生成
- `POST /api/v1/projects/{id}/script/generate-outline` — 生成/重生成大纲
- `POST /api/v1/projects/{id}/script/confirm-outline` — 确认大纲，进入人物生成
- `POST /api/v1/projects/{id}/script/generate-characters` — 生成人物小传
- `POST /api/v1/projects/{id}/script/confirm-characters` — 确认人物，进入剧本生成
- `POST /api/v1/projects/{id}/script/generate-episode/{n}` — 生成第 N 集剧本
- `POST /api/v1/projects/{id}/script/confirm` — 确认剧本，进入资产阶段

### 3.2 资产管理（Asset）

**核心能力：** 从剧本中 AI 自动提取资产，形成项目级统一资产库，分镜引用资产保证一致性。

**资产类型：**
- `character` — 人物资产
- `scene` — 场景资产
- `prop` — 道具资产

**新增数据模型：**

```
Asset（资产条目）
├── id
├── project_id
├── type: character | scene | prop
├── name — 资产名称
├── description — 详细描述（用于 AI 生成）
├── image_url — 形象/概念图 URL
├── metadata — JSON 扩展字段
│   ├── 人物：age, gender, personality, clothing, voice_type
│   ├── 场景：int_ext, time_of_day, atmosphere
│   └── 道具：category, appearance
├── reference_count — 被引用次数
└── source: ai_extracted | manual_added
```

```
AssetScriptMapping（资产-剧本映射）
├── asset_id
├── script_id
├── script_scene_id (nullable) — 出现在哪个场景
└── role — 该资产在此处的角色/用途
```

**核心功能：**
1. AI 从剧本自动提取资产（人物、场景、道具）
2. 资产列表展示，支持分类筛选
3. 资产详情编辑（修改描述、上传/重生成形象图）
4. AI 生成人物形象图 / 场景概念图
5. 资产合并去重（相似资产合并提示）
6. 资产引用关系查看（哪些分镜/场景用到了这个资产）

**API 接口：**
- `POST /api/v1/projects/{id}/assets/extract` — 从剧本提取资产
- `GET /api/v1/projects/{id}/assets` — 资产列表（按类型筛选）
- `POST /api/v1/projects/{id}/assets` — 手动添加资产
- `PUT /api/v1/assets/{id}` — 修改资产
- `DELETE /api/v1/assets/{id}` — 删除资产
- `POST /api/v1/assets/{id}/generate-image` — 生成资产形象图
- `POST /api/v1/projects/{id}/assets/confirm` — 确认资产，进入分镜阶段

### 3.3 分镜管理（Storyboard）

**核心能力：** 场景级分镜，一个剧本场景对应一个分镜，包含镜头设计和关键帧预览。

**新增数据模型：**

```
StoryboardShot（分镜镜头）
├── id
├── project_id
├── script_scene_id — 关联的剧本场景
├── shot_number — 镜头编号（如 "S01E01-001"）
├── order_index — 排序
├── composition — 景别：远景/全景/中景/近景/特写
├── camera_movement — 运镜：固定/推/拉/摇/移/跟
├── camera_angle — 角度：平视/仰视/俯视/侧视
├── visual_description — 画面详细描述（用于视频生成）
├── duration_seconds — 预估时长（秒）
├── key_frame_url — 关键帧预览图 URL
├── character_ids — 出场人物 ID 列表（JSON array）
├── prop_ids — 出现道具 ID 列表（JSON array）
└── status: draft | confirmed
```

**核心功能：**
1. AI 自动生成场景级分镜（基于剧本场景 + 资产信息）
2. 分镜列表（时间线视图 + 缩略图）
3. 分镜编辑器：调整景别、运镜、画面描述
4. AI 生成分镜关键帧预览图
5. 分镜拖拽重排序
6. 分镜版本对比

**API 接口：**
- `POST /api/v1/projects/{id}/storyboard/generate` — 自动生成分镜
- `GET /api/v1/projects/{id}/storyboard` — 分镜列表
- `PUT /api/v1/storyboard-shots/{id}` — 修改分镜
- `POST /api/v1/storyboard-shots/{id}/generate-keyframe` — 生成关键帧
- `POST /api/v1/projects/{id}/storyboard/confirm` — 确认分镜，进入视频阶段

### 3.4 视频合成（Video）

**核心能力：** 分步生成 + 人工确认，逐分镜生成视频片段，最后合成成片。

**新增数据模型：**

```
VideoClip（视频片段）
├── id
├── project_id
├── storyboard_shot_id — 关联的分镜
├── status: pending | queued | generating | done | failed
├── video_url — 视频文件地址
├── duration_seconds — 实际时长
├── error_message — 失败原因
├── retry_count — 重试次数
└── provider — 生成服务（如 sora / kling / runway）
```

```
AudioTrack（音频轨）
├── id
├── project_id
├── type: dialogue | bgm | sfx
├── asset_id — 关联的人物资产（配音时）
├── audio_url — 音频文件地址
├── duration_seconds
└── metadata — JSON（音色参数、音量等）
```

```
FinalVideo（最终成片）
├── id
├── project_id
├── version — 版本号（如 "v1.0"）
├── video_url — 最终视频地址
├── subtitle_url — 字幕文件地址
├── thumbnail_url — 封面图
├── duration_seconds
├── resolution — 分辨率（如 "1080x1920"）
└── status: generating | done | failed
```

**核心功能：**
1. 逐分镜生成视频片段（可选择单个/批量生成）
2. 片段生成状态实时追踪（队列/生成中/成功/失败）
3. 片段预览 + 单片段重生成
4. AI 配音合成（按角色音色分配）
5. 字幕自动生成 + 样式调整
6. BGM 推荐与选择
7. 最终合成（转场 + 音视频同步 + 字幕烧录）
8. 多版本成片管理

**API 接口：**
- `POST /api/v1/projects/{id}/video-clips/generate` — 批量生成视频片段
- `POST /api/v1/video-clips/{id}/regenerate` — 重生成单个片段
- `GET /api/v1/projects/{id}/video-clips` — 片段列表
- `POST /api/v1/projects/{id}/audio/generate-voices` — 生成配音
- `POST /api/v1/projects/{id}/audio/generate-subs` — 生成字幕
- `POST /api/v1/projects/{id}/final-video/compose` — 合成最终视频
- `GET /api/v1/projects/{id}/final-videos` — 成片版本列表

## 4. 前端页面设计

### 4.1 项目详情页（新增）

项目详情页是核心交互界面，采用顶部 Tab + 阶段导航的形式：

```
┌─────────────────────────────────────────────────────┐
│  项目名称：《xxx》  [当前阶段：剧本阶段]              │
├─────────────────────────────────────────────────────┤
│  📝 剧本  │  🎨 资产  │  🎬 分镜  │  🎥 视频  │  ✅ 成片 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  当前阶段的内容区域                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

- Tab 按阶段顺序排列，未解锁阶段置灰不可点击
- 当前阶段高亮显示
- 每个阶段底部有「确认并进入下一阶段」按钮

### 4.2 各阶段页面

| 页面路由 | 对应阶段 | 说明 |
|----------|----------|------|
| `/projects/:id/script` | 剧本阶段 | 剧本编辑器 + 分步引导面板 |
| `/projects/:id/assets` | 资产阶段 | 资产库（人物/场景/道具分类） |
| `/projects/:id/storyboard` | 分镜阶段 | 分镜时间线 + 分镜编辑器 |
| `/projects/:id/video` | 视频阶段 | 片段生成状态 + 配音 + 合成控制 |
| `/projects/:id/output` | 完成 | 成片版本列表 + 预览导出 |

## 5. 阶段流转规则

1. **进入下一阶段**：点击「确认并进入下一阶段」后，当前阶段数据被标记为 `confirmed`，项目 `phase` 推进到下一阶段。
2. **回退到上一阶段**：已确认的阶段可以点击「返回修改」，解锁当前阶段内容，回退到目标阶段。回退后下游数据保留但标记为「待更新」。
3. **数据一致性**：修改上游数据（如剧本）后，下游资产/分镜/视频需要提示用户是否重新生成。

## 6. 与现有代码的集成

### 6.1 现有模型调整

- `Project` 模型：新增 `phase` 字段（ProjectPhase 枚举），保留 `status` 用于 active/archived
- `Script` 模型：扩展 `source_type`, `source_text`, `outline` 等字段
- 现有 API 保持兼容，新增 v1 接口

### 6.2 新增模块

```
app/models/
├── asset.py          # 新增
├── storyboard.py     # 新增
└── video.py          # 新增

app/services/
├── asset_service.py       # 新增
├── storyboard_service.py  # 新增
└── video_service.py       # 新增

app/api/v1/
├── assets.py         # 新增
├── storyboard.py     # 新增
└── video.py          # 新增
```

## 7. 实施优先级

**P0（核心骨架）：**
- Project phase 字段 + 阶段流转
- 资产管理模块（数据模型 + CRUD + AI 提取）
- 分镜管理模块（数据模型 + CRUD + AI 生成）

**P1（核心流程打通）：**
- 剧本分步引导（小说导入 → 大纲 → 剧本）
- 视频片段生成（接入视频生成服务）
- 配音合成

**P2（完善体验）：**
- 关键帧预览图生成
- 字幕与 BGM
- 最终合成
- 版本历史与对比

## 8. 风险与依赖

1. **AI 服务依赖**：资产提取、分镜生成、视频生成都依赖 LLM 和视频生成 API，需要设计好异步任务队列和失败重试机制。
2. **数据量大**：视频文件体积大，需要规划好文件存储方案（本地 / S3）。
3. **生成时间长**：视频生成可能需要数分钟到数十分钟，需要完善的进度追踪和通知机制。
