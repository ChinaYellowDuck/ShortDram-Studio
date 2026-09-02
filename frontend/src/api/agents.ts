import { api } from './client'
import type { AgentChatResponse, AgentInfo } from './types'

export async function listAgents(): Promise<AgentInfo[]> {
  const { data } = await api.get<AgentInfo[]>('/agents/list')
  return data
}

export async function chatWithHelloAgent(
  message: string,
  llmConfigId?: number,
): Promise<AgentChatResponse> {
  const { data } = await api.post<AgentChatResponse>('/agents/hello/chat', null, {
    params: { message, llm_config_id: llmConfigId },
  })
  return data
}
