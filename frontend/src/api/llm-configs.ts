import { api } from './client'
import type { LLMConfig, LLMConfigCreate, LLMProvider, LLMTestResult, Paginated } from './types'

export async function listConfigs(params?: {
  page?: number
  page_size?: number
}): Promise<Paginated<LLMConfig>> {
  const { data } = await api.get<Paginated<LLMConfig>>('/llm-configs', { params })
  return data
}

export async function getProviders(): Promise<LLMProvider[]> {
  const { data } = await api.get<LLMProvider[]>('/llm-configs/providers')
  return data
}

export async function createConfig(payload: LLMConfigCreate): Promise<LLMConfig> {
  const { data } = await api.post<LLMConfig>('/llm-configs', payload)
  return data
}

export async function deleteConfig(id: number): Promise<void> {
  await api.delete(`/llm-configs/${id}`)
}

export async function setDefaultConfig(id: number): Promise<LLMConfig> {
  const { data } = await api.post<LLMConfig>(`/llm-configs/${id}/set-default`)
  return data
}

export async function testConfig(id: number): Promise<LLMTestResult> {
  const { data } = await api.post<LLMTestResult>(`/llm-configs/${id}/test`)
  return data
}
