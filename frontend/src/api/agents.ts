import { api } from './client'
import type { AgentChatResponse, AgentInfo, AgentMetadata, Paginated } from './types'

export async function listAgents(): Promise<AgentInfo[]> {
  const { data } = await api.get<AgentInfo[]>('/agents/list')
  return data
}

export async function listAgentMetadata(): Promise<Paginated<AgentMetadata>> {
  const { data } = await api.get<Paginated<AgentMetadata>>('/agents/meta', {
    params: { page: 1, page_size: 100 },
  })
  return data
}

export async function updateAgentMetadata(
  id: number,
  payload: Partial<AgentMetadata>,
): Promise<AgentMetadata> {
  const { data } = await api.put<AgentMetadata>(`/agents/meta/${id}`, payload)
  return data
}

export async function setAgentEnabled(id: number, enabled: boolean): Promise<AgentMetadata> {
  const { data } = await api.patch<AgentMetadata>(`/agents/meta/${id}/enabled`, null, {
    params: { enabled },
  })
  return data
}

export async function listAgentMcpTools(agentId: number): Promise<{
  tools: Array<Record<string, unknown>>
  total: number
}> {
  const { data } = await api.get(`/agents/meta/${agentId}/mcp-tools`)
  return data
}

export async function chatWithAgent(
  agentKey: string,
  message: string,
  llmConfigId?: number,
): Promise<AgentChatResponse> {
  const { data } = await api.post<AgentChatResponse>('/agents/chat', null, {
    params: { agent_key: agentKey, message, llm_config_id: llmConfigId },
  })
  return data
}
