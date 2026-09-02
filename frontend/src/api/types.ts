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
