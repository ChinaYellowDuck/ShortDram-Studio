import { api } from './client'
import type {
  Asset,
  AssetCreate,
  AssetType,
  AssetUpdate,
  Paginated,
} from './types'

export async function listAssets(params: {
  project_id: number
  page?: number
  page_size?: number
  type?: AssetType
  search?: string
}): Promise<Paginated<Asset>> {
  const { data } = await api.get<Paginated<Asset>>('/assets', { params })
  return data
}

export async function getAsset(id: number): Promise<Asset> {
  const { data } = await api.get<Asset>(`/assets/${id}`)
  return data
}

export async function createAsset(
  project_id: number,
  payload: AssetCreate,
): Promise<Asset> {
  const { data } = await api.post<Asset>('/assets', payload, {
    params: { project_id },
  })
  return data
}

export async function updateAsset(
  id: number,
  payload: AssetUpdate,
): Promise<Asset> {
  const { data } = await api.put<Asset>(`/assets/${id}`, payload)
  return data
}

export async function deleteAsset(id: number): Promise<void> {
  await api.delete(`/assets/${id}`)
}
