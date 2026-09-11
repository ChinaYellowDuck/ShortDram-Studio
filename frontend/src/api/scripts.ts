import { api } from './client'
import type {
  CharactersGenerateRequest,
  FountainExport,
  OutlineGenerateRequest,
  Paginated,
  ProducerCreateResponse,
  SceneRefineResponse,
  Script,
  ScriptCharacter,
  ScriptCharacterCreate,
  ScriptCharacterUpdate,
  ScriptDetail,
  ScriptDialogue,
  ScriptDialogueCreate,
  ScriptDialogueUpdate,
  ScriptEpisode,
  ScriptEpisodeCreate,
  ScriptEpisodeUpdate,
  ScriptGenerateRequest,
  ScriptGenerateResponse,
  ScriptScene,
  ScriptSceneCreate,
  ScriptSceneUpdate,
  ScriptUpdate,
} from './types'

// ── Script ──────────────────────────────────────────────────────────────────

export async function listScripts(
  projectId: number,
  params?: { page?: number; page_size?: number },
): Promise<Paginated<Script>> {
  const { data } = await api.get<Paginated<Script>>(`/scripts/project/${projectId}`, { params })
  return data
}

export async function getScript(scriptId: number): Promise<ScriptDetail> {
  const { data } = await api.get<ScriptDetail>(`/scripts/${scriptId}`)
  return data
}

export async function createScript(payload: {
  project_id: number
  title: string
  logline?: string | null
  genre?: string | null
  style?: string | null
  total_episodes?: number
  synopsis?: string | null
}): Promise<Script> {
  const { data } = await api.post<Script>('/scripts', payload)
  return data
}

export async function updateScript(scriptId: number, payload: ScriptUpdate): Promise<Script> {
  const { data } = await api.put<Script>(`/scripts/${scriptId}`, payload)
  return data
}

export async function deleteScript(scriptId: number): Promise<void> {
  await api.delete(`/scripts/${scriptId}`)
}

export async function importScriptText(
  scriptId: number,
  text: string,
  sourceType: 'auto' | 'novel' | 'fountain' = 'auto',
): Promise<{ format: string; scenes: number; dialogues: number; characters: number }> {
  const { data } = await api.post(
    `/scripts/${scriptId}/import/text`,
    null,
    { params: { text, source_type: sourceType } },
  )
  return data
}

export async function importScriptFile(
  scriptId: number,
  file: File,
  sourceType: 'auto' | 'novel' | 'fountain' = 'auto',
): Promise<{ format: string; scenes: number; dialogues: number; characters: number }> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post(
    `/scripts/${scriptId}/import/file`,
    formData,
    { params: { source_type: sourceType } },
  )
  return data
}

export async function exportFountain(scriptId: number): Promise<FountainExport> {
  const { data } = await api.get<FountainExport>(`/scripts/${scriptId}/export/fountain`)
  return data
}

// ── Episode ─────────────────────────────────────────────────────────────────

export async function listEpisodes(scriptId: number): Promise<ScriptEpisode[]> {
  const { data } = await api.get<ScriptEpisode[]>(`/scripts/${scriptId}/episodes`)
  return data
}

export async function createEpisode(
  scriptId: number,
  payload: ScriptEpisodeCreate,
): Promise<ScriptEpisode> {
  const { data } = await api.post<ScriptEpisode>(`/scripts/${scriptId}/episodes`, payload)
  return data
}

export async function getEpisode(episodeId: number): Promise<ScriptEpisode> {
  const { data } = await api.get<ScriptEpisode>(`/scripts/episodes/${episodeId}`)
  return data
}

export async function updateEpisode(
  episodeId: number,
  payload: ScriptEpisodeUpdate,
): Promise<ScriptEpisode> {
  const { data } = await api.put<ScriptEpisode>(`/scripts/episodes/${episodeId}`, payload)
  return data
}

export async function deleteEpisode(episodeId: number): Promise<void> {
  await api.delete(`/scripts/episodes/${episodeId}`)
}

// ── Wizard / Generation ─────────────────────────────────────────────────────

export async function generateOutline(
  scriptId: number,
  payload: OutlineGenerateRequest,
): Promise<ScriptDetail> {
  const { data } = await api.post<ScriptDetail>(
    `/scripts/${scriptId}/outline/generate`,
    payload,
  )
  return data
}

export async function generateCharacters(
  scriptId: number,
  payload: CharactersGenerateRequest,
): Promise<ScriptCharacter[]> {
  const { data } = await api.post<ScriptCharacter[]>(
    `/scripts/${scriptId}/characters/generate`,
    payload,
  )
  return data
}

export async function generateEpisodeScript(
  scriptId: number,
  episodeNumber: number,
): Promise<ScriptEpisode> {
  const { data } = await api.post<ScriptEpisode>(
    `/scripts/${scriptId}/episodes/${episodeNumber}/generate`,
  )
  return data
}

// ── Scene ───────────────────────────────────────────────────────────────────

export async function listScenes(scriptId: number): Promise<ScriptScene[]> {
  const { data } = await api.get<ScriptScene[]>(`/scripts/${scriptId}/scenes`)
  return data
}

export async function getScene(sceneId: number): Promise<ScriptScene> {
  const { data } = await api.get<ScriptScene>(`/scripts/scenes/${sceneId}`)
  return data
}

export async function createScene(
  scriptId: number,
  payload: ScriptSceneCreate,
): Promise<ScriptScene> {
  const { data } = await api.post<ScriptScene>(`/scripts/${scriptId}/scenes`, payload)
  return data
}

export async function updateScene(
  sceneId: number,
  payload: ScriptSceneUpdate,
): Promise<ScriptScene> {
  const { data } = await api.put<ScriptScene>(`/scripts/scenes/${sceneId}`, payload)
  return data
}

export async function deleteScene(sceneId: number): Promise<void> {
  await api.delete(`/scripts/scenes/${sceneId}`)
}

// ── Character ───────────────────────────────────────────────────────────────

export async function listCharacters(scriptId: number): Promise<ScriptCharacter[]> {
  const { data } = await api.get<ScriptCharacter[]>(`/scripts/${scriptId}/characters`)
  return data
}

export async function createCharacter(
  scriptId: number,
  payload: ScriptCharacterCreate,
): Promise<ScriptCharacter> {
  const { data } = await api.post<ScriptCharacter>(`/scripts/${scriptId}/characters`, payload)
  return data
}

export async function updateCharacter(
  characterId: number,
  payload: ScriptCharacterUpdate,
): Promise<ScriptCharacter> {
  const { data } = await api.put<ScriptCharacter>(
    `/scripts/characters/${characterId}`,
    payload,
  )
  return data
}

export async function deleteCharacter(characterId: number): Promise<void> {
  await api.delete(`/scripts/characters/${characterId}`)
}

// ── Dialogue ────────────────────────────────────────────────────────────────

export async function listDialogues(sceneId: number): Promise<ScriptDialogue[]> {
  const { data } = await api.get<ScriptDialogue[]>(`/scripts/scenes/${sceneId}/dialogues`)
  return data
}

export async function createDialogue(
  sceneId: number,
  payload: ScriptDialogueCreate,
): Promise<ScriptDialogue> {
  const { data } = await api.post<ScriptDialogue>(
    `/scripts/scenes/${sceneId}/dialogues`,
    payload,
  )
  return data
}

export async function updateDialogue(
  dialogueId: number,
  payload: ScriptDialogueUpdate,
): Promise<ScriptDialogue> {
  const { data } = await api.put<ScriptDialogue>(
    `/scripts/dialogues/${dialogueId}`,
    payload,
  )
  return data
}

export async function deleteDialogue(dialogueId: number): Promise<void> {
  await api.delete(`/scripts/dialogues/${dialogueId}`)
}

// ── Agent endpoints (script generation) ─────────────────────────────────────

export async function generateScript(
  payload: ScriptGenerateRequest,
): Promise<ScriptGenerateResponse> {
  const { data } = await api.post<ScriptGenerateResponse>(
    '/agents/screenwriter/generate',
    payload,
  )
  return data
}

export async function createProjectWithProducer(
  payload: ScriptGenerateRequest,
): Promise<ProducerCreateResponse> {
  const { data } = await api.post<ProducerCreateResponse>(
    '/agents/producer/create-project',
    payload,
  )
  return data
}

export async function refineScene(payload: {
  script_id: number
  scene_id: number
  feedback: string
  llm_config_id?: number
}): Promise<SceneRefineResponse> {
  const { data } = await api.post<SceneRefineResponse>('/agents/screenwriter/refine', payload)
  return data
}
