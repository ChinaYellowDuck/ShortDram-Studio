/** 与后端 Pydantic schema 对应的前端类型定义 */

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type ProjectStatus = 'draft' | 'in_progress' | 'completed' | 'archived'
export type ProjectPhase = 'setup' | 'script' | 'asset' | 'storyboard' | 'video' | 'completed'

export interface Project {
  id: number
  name: string
  description: string | null
  cover_image: string | null
  status: ProjectStatus
  phase: ProjectPhase
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string | null
  cover_image?: string | null
  status?: ProjectStatus
  phase?: ProjectPhase
}

export interface PhaseTransition {
  target_phase: ProjectPhase
}

export interface LLMConfig {
  id: number
  name: string
  provider: string
  model_type: 'text' | 'image' | 'video' | 'audio'
  model_name: string
  base_url: string | null
  description: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface LLMConfigCreate {
  name: string
  provider: string
  model_type?: 'text' | 'image' | 'video' | 'audio'
  model_name: string
  api_key: string
  base_url?: string | null
  description?: string | null
  is_default?: boolean
}

export interface LLMProvider {
  key: string
  name: string
  default_model: string
  supports_base_url: boolean
}

export interface LLMTestResult {
  success: boolean
  message: string
  response_time_ms: number | null
  model: string | null
}

export interface AgentInfo {
  id: number
  agent_key: string
  name: string
  description: string
  status: string
  category: string
  default_llm_config_id: number | null
}

export interface AgentMetadata {
  id: number
  agent_key: string
  name: string
  description: string | null
  agent_type: string
  category: string | null
  is_enabled: boolean
  default_llm_config_id: number | null
  default_params: Record<string, unknown> | null
  temperature: number
  system_message: string | null
  mcp_ids: number[]
  skill_ids: number[]
  version: string
  created_at: string
  updated_at: string
}

export interface Mcp {
  id: number
  name: string
  url: string
  transport: string
  mcp_type: string
  config: Record<string, unknown> | null
  secrets: Record<string, unknown> | null
  tools: Array<Record<string, unknown>> | null
  description: string | null
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface McpCreate {
  name: string
  url: string
  transport?: string
  mcp_type?: string
  config?: Record<string, unknown> | null
  secrets?: Record<string, unknown> | null
  description?: string | null
  is_enabled?: boolean
}

export interface McpUpdate {
  name?: string
  url?: string
  transport?: string
  mcp_type?: string
  config?: Record<string, unknown> | null
  secrets?: Record<string, unknown> | null
  description?: string | null
  is_enabled?: boolean
}

export interface McpTestResult {
  ok: boolean
  error?: string
  tools?: Array<Record<string, unknown>>
  server_version?: string
  latency_ms?: number
}

export interface Skill {
  id: number
  name: string
  description: string | null
  content: string
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface SkillCreate {
  name: string
  description?: string | null
  content: string
  is_enabled?: boolean
}

export interface AgentChatResponse {
  agent: string
  run_id: number
  message: string
  response: string
  llm_config: {
    id: number
    name: string
    provider: string
    model: string
  }
}

export interface ServiceHealth {
  status: string
  error: string | null
}

export interface HealthStatus {
  status: string
  version: string
  env: string
  services: {
    database: ServiceHealth
    redis: ServiceHealth
  }
}

export interface LangsmithStatus {
  enabled: boolean
  project: string | null
  endpoint: string | null
}

export interface RootInfo {
  name: string
  version: string
  status: string
  docs: string
}

// ── Script types ────────────────────────────────────────────────────────────

export type ScriptGenerationStage = 'idea' | 'outline' | 'characters' | 'episodes' | 'completed'
export type IntExt = 'INT' | 'EXT' | 'INT/EXT'
export type TimeOfDay = '日' | '夜' | '晨' | '昏' | '不限'
export type CharacterType = '主角' | '配角' | '客串' | '龙套'
export type Emotion =
  | '正常'
  | '开心'
  | '悲伤'
  | '愤怒'
  | '惊讶'
  | '恐惧'
  | '紧张'
  | '平静'
  | '兴奋'
  | '自信'
  | '讽刺'
  | '冷漠'
  | '温柔'

export interface ScriptCharacter {
  id: number
  script_id: number
  name: string
  description: string | null
  character_type: CharacterType
  age: string | null
  appearance: string | null
  created_at: string
  updated_at: string
}

export interface ScriptCharacterCreate {
  name: string
  description?: string | null
  character_type?: CharacterType
  age?: string | null
  appearance?: string | null
}

export interface ScriptCharacterUpdate {
  name?: string
  description?: string | null
  character_type?: CharacterType
  age?: string | null
  appearance?: string | null
}

export interface ScriptDialogue {
  id: number
  scene_id: number
  character_id: number | null
  character_name: string
  dialogue: string
  action: string | null
  emotion: Emotion
  order_index: number
  created_at: string
  updated_at: string
}

export interface ScriptDialogueCreate {
  character_name: string
  dialogue: string
  action?: string | null
  emotion?: Emotion
  character_id?: number | null
  order_index?: number
}

export interface ScriptDialogueUpdate {
  character_name?: string
  dialogue?: string
  action?: string | null
  emotion?: Emotion
  character_id?: number | null
  order_index?: number
}

export interface ScriptScene {
  id: number
  script_id: number
  scene_number: string
  location: string
  int_ext: IntExt
  time_of_day: TimeOfDay
  description: string | null
  order_index: number
  dialogues: ScriptDialogue[]
  created_at: string
  updated_at: string
}

export interface ScriptSceneCreate {
  scene_number: string
  location: string
  int_ext?: IntExt
  time_of_day?: TimeOfDay
  description?: string | null
  order_index?: number
}

export interface ScriptSceneUpdate {
  scene_number?: string
  location?: string
  int_ext?: IntExt
  time_of_day?: TimeOfDay
  description?: string | null
  order_index?: number
}

export interface Script {
  id: number
  project_id: number
  title: string
  logline: string | null
  genre: string | null
  style: string | null
  total_episodes: number
  synopsis: string | null
  version: string
  generation_stage: ScriptGenerationStage
  episode_outlines: Record<string, unknown>[] | null
  core_idea: string | null
  created_at: string
  updated_at: string
}

export interface ScriptDetail extends Script {
  scenes: ScriptScene[]
  characters: ScriptCharacter[]
  episodes: ScriptEpisode[]
}

export interface ScriptCreate {
  project_id: number
  title: string
  logline?: string | null
  genre?: string | null
  style?: string | null
  total_episodes?: number
  synopsis?: string | null
  version?: string
  generation_stage?: ScriptGenerationStage
  core_idea?: string | null
}

export interface ScriptUpdate {
  title?: string
  logline?: string | null
  genre?: string | null
  style?: string | null
  total_episodes?: number
  synopsis?: string | null
  version?: string
  generation_stage?: ScriptGenerationStage
  episode_outlines?: Record<string, unknown>[] | null
  core_idea?: string | null
}

export interface ScriptGenerateRequest {
  idea: string
  genre?: string
  style?: string
  num_scenes?: number
  llm_config_id?: number
}

export interface GeneratedCharacter {
  name: string
  description?: string | null
  role?: string
  age?: string | null
  appearance?: string | null
  personality?: string | null
}

export interface GeneratedDialogue {
  character_name: string
  dialogue: string
  action?: string | null
  emotion?: string
}

export interface GeneratedScene {
  scene_number?: string | number
  location?: string
  int_ext?: string
  time_of_day?: string
  description?: string | null
  order_index?: number
  dialogues?: GeneratedDialogue[]
}

export interface ScriptGenerateResult {
  logline: string
  synopsis: string
  genre: string
  style: string
  characters: GeneratedCharacter[]
  scenes: GeneratedScene[]
  review: Record<string, unknown>
  current_stage: string
  error: string
}

export interface ScriptGenerateResponse {
  agent: string
  run_id: number
  llm_config: {
    id: number
    name: string
    provider: string
    model: string
  }
  result: ScriptGenerateResult
}

export interface ProducerCreateResponse {
  agent: string
  run_id: number
  project_id: number
  script_id: number
  validation: Record<string, unknown>
  llm_config: {
    id: number
    name: string
    provider: string
    model: string
  }
  result: {
    project_name: string
    logline: string
    synopsis: string
    num_characters: number
    num_scenes: number
    review: Record<string, unknown>
  }
  current_stage: string
}

export interface SceneRefineResponse {
  agent: string
  run_id: number
  action: string
  scene_id: number
  feedback: string
  llm_config: {
    id: number
    name: string
    provider: string
    model: string
  }
  refined_scene: {
    description: string | null
    dialogues: ScriptDialogueCreate[]
    [key: string]: unknown
  }
}

export interface FountainExport {
  script_id: number
  title: string
  content: string
  format: string
}

// ── Asset types ─────────────────────────────────────────────────────────────

export type AssetType = 'character' | 'scene' | 'prop'
export type AssetSource = 'ai_extracted' | 'manual'

export interface Asset {
  id: number
  project_id: number
  type: AssetType
  name: string
  description: string | null
  image_url: string | null
  extra: Record<string, unknown> | null
  source: AssetSource
  reference_count: number
  created_at: string
  updated_at: string
}

export interface AssetCreate {
  type: AssetType
  name: string
  description?: string | null
  image_url?: string | null
  extra?: Record<string, unknown> | null
  source?: AssetSource
  reference_count?: number
}

export interface AssetUpdate {
  type?: AssetType
  name?: string
  description?: string | null
  image_url?: string | null
  extra?: Record<string, unknown> | null
  source?: AssetSource
  reference_count?: number
}

// ── Storyboard types ───────────────────────────────────────────────────────

export type CompositionType = '大远景' | '远景' | '全景' | '中景' | '中近景' | '近景' | '特写'
export type CameraMovement = '固定' | '推' | '拉' | '摇' | '移' | '跟' | '变焦'
export type CameraAngle = '平视' | '仰视' | '俯视' | '侧视' | '倾斜'

export interface StoryboardShot {
  id: number
  project_id: number
  script_scene_id: number
  shot_number: string
  order_index: number
  composition: CompositionType
  camera_movement: CameraMovement
  camera_angle: CameraAngle
  visual_description: string | null
  duration_seconds: number
  key_frame_url: string | null
  character_ids: number[] | null
  prop_ids: number[] | null
  created_at: string
  updated_at: string
}

export interface StoryboardShotCreate {
  script_scene_id: number
  shot_number: string
  order_index?: number
  composition?: CompositionType
  camera_movement?: CameraMovement
  camera_angle?: CameraAngle
  visual_description?: string | null
  duration_seconds?: number
  key_frame_url?: string | null
  character_ids?: number[] | null
  prop_ids?: number[] | null
}

export interface StoryboardShotUpdate {
  script_scene_id?: number
  shot_number?: string
  order_index?: number
  composition?: CompositionType
  camera_movement?: CameraMovement
  camera_angle?: CameraAngle
  visual_description?: string | null
  duration_seconds?: number
  key_frame_url?: string | null
  character_ids?: number[] | null
  prop_ids?: number[] | null
}

export interface ReorderRequest {
  shot_ids: number[]
}

// ── Project Agent Config types ──────────────────────────────────────────

export interface AgentSimple {
  id: number
  agent_key: string
  name: string
  description: string | null
  agent_type: string
  category: string | null
  is_enabled: boolean
  temperature: number
  version: string
}

export interface ProjectAgentConfig {
  id: number
  project_id: number
  agent_id: number
  is_enabled: boolean
  is_director: boolean
  llm_config_id: number | null
  params_override: Record<string, unknown> | null
  temperature: number | null
  system_message_override: string | null
  priority: number
  role_description: string | null
  created_at: string
  updated_at: string
  agent_key: string | null
  agent_name: string | null
  agent_description: string | null
  agent_type: string | null
  agent_category: string | null
}

export interface ProjectAgentSetupRequest {
  director_agent_id: number
  enabled_agent_ids: number[]
}

export interface ProjectAgentConfigUpdate {
  is_enabled?: boolean
  is_director?: boolean
  llm_config_id?: number | null
  params_override?: Record<string, unknown> | null
  temperature?: number | null
  system_message_override?: string | null
  priority?: number
  role_description?: string | null
}

// ── Script Episode types ────────────────────────────────────────────────────

export interface ScriptEpisode {
  id: number
  script_id: number
  episode_number: number
  title: string | null
  synopsis: string | null
  duration_seconds: number | null
  is_generated: boolean
  order_index: number
  created_at: string
  updated_at: string
}

export interface ScriptEpisodeCreate {
  episode_number: number
  title?: string | null
  synopsis?: string | null
  duration_seconds?: number | null
  is_generated?: boolean
  order_index?: number
}

export interface ScriptEpisodeUpdate {
  episode_number?: number
  title?: string | null
  synopsis?: string | null
  duration_seconds?: number | null
  is_generated?: boolean
  order_index?: number
}

// ── Script Wizard Request types ─────────────────────────────────────────────

export interface OutlineGenerateRequest {
  idea: string
  genre?: string
  style?: string
  total_episodes?: number
  llm_config_id?: number
}

export interface CharactersGenerateRequest {
  num_characters?: number
  llm_config_id?: number
}
