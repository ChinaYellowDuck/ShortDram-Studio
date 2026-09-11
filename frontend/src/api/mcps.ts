import { api } from './client'
import type { Mcp, McpCreate, McpTestResult, McpUpdate, Paginated } from './types'

export async function listMcps(params?: {
  page?: number
  page_size?: number
  is_enabled?: boolean
  mcp_type?: string
  search?: string
}): Promise<Paginated<Mcp>> {
  const { data } = await api.get<Paginated<Mcp>>('/mcps', { params })
  return data
}

export async function createMcp(payload: McpCreate): Promise<Mcp> {
  const { data } = await api.post<Mcp>('/mcps', payload)
  return data
}

export async function updateMcp(id: number, payload: McpUpdate): Promise<Mcp> {
  const { data } = await api.put<Mcp>(`/mcps/${id}`, payload)
  return data
}

export async function deleteMcp(id: number): Promise<void> {
  await api.delete(`/mcps/${id}`)
}

export async function testMcpConnection(payload: {
  url: string
  transport?: string
  config?: Record<string, unknown> | null
  secrets?: Record<string, unknown> | null
}): Promise<McpTestResult> {
  const { data } = await api.post<McpTestResult>('/mcps/test-connection', payload)
  return data
}

export async function testExistingMcp(id: number): Promise<McpTestResult> {
  const { data } = await api.post<McpTestResult>(`/mcps/${id}/test-connection`)
  return data
}

export async function refreshMcpTools(id: number): Promise<{ tools: Array<Record<string, unknown>>; count: number }> {
  const { data } = await api.post(`/mcps/${id}/refresh-tools`)
  return data
}
