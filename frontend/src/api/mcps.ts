import { api } from './client'
import type { Mcp, McpCreate, Paginated } from './types'

export async function listMcps(params?: {
  page?: number
  page_size?: number
  is_enabled?: boolean
  search?: string
}): Promise<Paginated<Mcp>> {
  const { data } = await api.get<Paginated<Mcp>>('/mcps', { params })
  return data
}

export async function createMcp(payload: McpCreate): Promise<Mcp> {
  const { data } = await api.post<Mcp>('/mcps', payload)
  return data
}

export async function updateMcp(id: number, payload: Partial<McpCreate>): Promise<Mcp> {
  const { data } = await api.put<Mcp>(`/mcps/${id}`, payload)
  return data
}

export async function deleteMcp(id: number): Promise<void> {
  await api.delete(`/mcps/${id}`)
}
