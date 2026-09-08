import { api } from './client'
import type { Paginated, Skill, SkillCreate } from './types'

export async function listSkills(params?: {
  page?: number
  page_size?: number
  is_enabled?: boolean
  search?: string
}): Promise<Paginated<Skill>> {
  const { data } = await api.get<Paginated<Skill>>('/skills', { params })
  return data
}

export async function createSkill(payload: SkillCreate): Promise<Skill> {
  const { data } = await api.post<Skill>('/skills', payload)
  return data
}

export async function updateSkill(id: number, payload: Partial<SkillCreate>): Promise<Skill> {
  const { data } = await api.put<Skill>(`/skills/${id}`, payload)
  return data
}

export async function deleteSkill(id: number): Promise<void> {
  await api.delete(`/skills/${id}`)
}
