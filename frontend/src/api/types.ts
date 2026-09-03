/** 与后端 Pydantic schema 对应的前端类型定义 */

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export type ProjectStatus = 'draft' | 'in_progress' | 'completed' | 'archived'

export interface Project {
  id: number
  name: string
  description: string | null
  cover_image: string | null
  status: ProjectStatus
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  description?: string | null
  cover_image?: string | null
  status?: ProjectStatus
}

export interface LLMConfig {
  id: number
  name: string
  provider: string
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
  id: string
  name: string
  description: string
  status: string
}

export interface AgentChatResponse {
  agent: string
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
  created_at: string
  updated_at: string
}

export interface ScriptDetail extends Script {
  scenes: ScriptScene[]
  characters: ScriptCharacter[]
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
}

export interface ScriptUpdate {
  title?: string
  logline?: string | null
  genre?: string | null
  style?: string | null
  total_episodes?: number
  synopsis?: string | null
  version?: string
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
