import { api } from './client'
import type {
  AgentSimple,
  ProjectAgentConfig,
  ProjectAgentConfigUpdate,
  ProjectAgentSetupRequest,
} from './types'

// ── Global agent registry ────────────────────────────────────────────────

export async function listAvailableAgents(): Promise<AgentSimple[]> {
  const { data } = await api.get<AgentSimple[]>('/agents')
  return data
}

// ── Project agent configs ────────────────────────────────────────────────

export async function listProjectAgents(projectId: number): Promise<ProjectAgentConfig[]> {
  const { data } = await api.get<ProjectAgentConfig[]>(`/projects/${projectId}/agents`)
  return data
}

export async function listEnabledProjectAgents(projectId: number): Promise<ProjectAgentConfig[]> {
  const { data } = await api.get<ProjectAgentConfig[]>(`/projects/${projectId}/agents/enabled`)
  return data
}

export async function getDirectorAgent(projectId: number): Promise<ProjectAgentConfig> {
  const { data } = await api.get<ProjectAgentConfig>(`/projects/${projectId}/agents/director`)
  return data
}

export async function setupProjectAgents(
  projectId: number,
  payload: ProjectAgentSetupRequest,
): Promise<ProjectAgentConfig[]> {
  const { data } = await api.post<ProjectAgentConfig[]>(
    `/projects/${projectId}/agents/setup`,
    payload,
  )
  return data
}

export async function updateProjectAgent(
  projectId: number,
  agentId: number,
  payload: ProjectAgentConfigUpdate,
): Promise<ProjectAgentConfig> {
  const { data } = await api.put<ProjectAgentConfig>(
    `/projects/${projectId}/agents/${agentId}`,
    payload,
  )
  return data
}

export async function toggleProjectAgent(
  projectId: number,
  agentId: number,
): Promise<ProjectAgentConfig> {
  const { data } = await api.post<ProjectAgentConfig>(
    `/projects/${projectId}/agents/${agentId}/toggle`,
  )
  return data
}

export async function removeProjectAgent(projectId: number, agentId: number): Promise<void> {
  await api.delete(`/projects/${projectId}/agents/${agentId}`)
}
