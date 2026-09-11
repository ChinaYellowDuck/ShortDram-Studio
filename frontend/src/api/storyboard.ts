import { api } from './client'
import type {
  Paginated,
  ReorderRequest,
  StoryboardShot,
  StoryboardShotCreate,
  StoryboardShotUpdate,
} from './types'

export async function listStoryboardShots(params: {
  project_id: number
  page?: number
  page_size?: number
}): Promise<Paginated<StoryboardShot>> {
  const { data } = await api.get<Paginated<StoryboardShot>>('/storyboard', {
    params,
  })
  return data
}

export async function getStoryboardShot(id: number): Promise<StoryboardShot> {
  const { data } = await api.get<StoryboardShot>(`/storyboard/${id}`)
  return data
}

export async function createStoryboardShot(
  project_id: number,
  payload: StoryboardShotCreate,
): Promise<StoryboardShot> {
  const { data } = await api.post<StoryboardShot>('/storyboard', payload, {
    params: { project_id },
  })
  return data
}

export async function updateStoryboardShot(
  id: number,
  payload: StoryboardShotUpdate,
): Promise<StoryboardShot> {
  const { data } = await api.put<StoryboardShot>(`/storyboard/${id}`, payload)
  return data
}

export async function deleteStoryboardShot(id: number): Promise<void> {
  await api.delete(`/storyboard/${id}`)
}

export async function reorderStoryboard(
  project_id: number,
  shot_ids: number[],
): Promise<StoryboardShot[]> {
  const { data } = await api.post<StoryboardShot[]>(
    '/storyboard/reorder',
    { shot_ids } satisfies ReorderRequest,
    { params: { project_id } },
  )
  return data
}
