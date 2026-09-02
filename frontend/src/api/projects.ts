import { api } from './client'
import type { Paginated, Project, ProjectCreate, ProjectStatus } from './types'

export async function listProjects(params?: {
  page?: number
  page_size?: number
  status?: ProjectStatus
  search?: string
}): Promise<Paginated<Project>> {
  const { data } = await api.get<Paginated<Project>>('/projects', { params })
  return data
}

export async function createProject(payload: ProjectCreate): Promise<Project> {
  const { data } = await api.post<Project>('/projects', payload)
  return data
}

export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/projects/${id}`)
}

export async function updateProjectStatus(id: number, status: ProjectStatus): Promise<Project> {
  // 后端 PATCH /projects/{id}/status?new_status=xxx
  const { data } = await api.patch<Project>(`/projects/${id}/status`, null, {
    params: { new_status: status },
  })
  return data
}
