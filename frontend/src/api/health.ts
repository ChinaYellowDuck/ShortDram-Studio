import { api } from './client'
import type { HealthStatus, LangsmithStatus, RootInfo } from './types'

export async function getRoot(): Promise<RootInfo> {
  // 根端点在后端是 `/`（不在 /api/v1 前缀下）
  const { data } = await api.get<RootInfo>('/', { baseURL: '/' })
  return data
}

export async function getHealth(): Promise<HealthStatus> {
  const { data } = await api.get<HealthStatus>('/health')
  return data
}

export async function getLangsmithStatus(): Promise<LangsmithStatus> {
  const { data } = await api.get<LangsmithStatus>('/health/langsmith')
  return data
}
