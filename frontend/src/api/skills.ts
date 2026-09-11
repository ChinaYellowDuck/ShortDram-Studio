import { api } from './client'
import type { Paginated, Skill, SkillCreate, SkillImportResult } from './types'

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

export async function importSkillFromText(payload: {
  text: string
  name?: string
  description?: string
  overwrite?: boolean
}): Promise<SkillImportResult> {
  const { data } = await api.post<SkillImportResult>('/skills/import/text', payload)
  return data
}

export async function importSkillsBatch(payload: {
  skills: Array<Record<string, unknown>>
  overwrite?: boolean
}): Promise<SkillImportResult> {
  const { data } = await api.post<SkillImportResult>('/skills/import/batch', payload)
  return data
}

export async function importSkillFromFile(
  file: File,
  overwrite = false,
): Promise<SkillImportResult> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<SkillImportResult>('/skills/import/file', formData, {
    params: { overwrite },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}
