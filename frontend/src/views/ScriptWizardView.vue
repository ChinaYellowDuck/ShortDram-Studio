<script setup lang="ts">
import { ArrowLeft, Check, MagicStick, Notebook, Setting, Upload, UploadFilled, User, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorMessage } from '../api/client'
import { listAvailableAgents, listProjectAgents, setupProjectAgents } from '../api/projectAgents'
import {
  createScript,
  generateCharacters,
  generateEpisodeScript,
  generateOutline,
  getScript,
  importScriptFile,
  importScriptText,
  listCharacters,
  listEpisodes,
  listScripts,
  updateScript,
} from '../api/scripts'
import type {
  AgentSimple,
  ProjectAgentConfig,
  ScriptDetail,
  ScriptCharacter,
  ScriptEpisode,
} from '../api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.projectId))

// ── 步骤配置 ──────────────────────────────────────────────
const steps = [
  { key: 'agents', label: '智能体配置', icon: Setting, desc: '选择总控与创作智能体' },
  { key: 'idea', label: '创意输入', icon: Notebook, desc: '描述你的短剧创意' },
  { key: 'outline', label: '故事大纲', icon: MagicStick, desc: '生成故事大纲与分集' },
  { key: 'characters', label: '人物设定', icon: User, desc: '设计主要人物档案' },
  { key: 'episodes', label: '逐集剧本', icon: VideoPlay, desc: '生成每集详细剧本' },
] as const

type WizardStep = typeof steps[number]['key']
const activeStep = ref<WizardStep>('agents')
const script = ref<ScriptDetail | null>(null)
const scriptId = ref<number | null>(null)
const loading = ref(false)
const generating = ref(false)

// ── Step 0: 智能体配置 ────────────────────────────────────
const availableAgents = ref<AgentSimple[]>([])
const projectAgents = ref<ProjectAgentConfig[]>([])
const agentsLoading = ref(false)
const directorAgentId = ref<number | null>(null)
const enabledAgentIds = ref<number[]>([])
const savingAgents = ref(false)

async function loadAgentConfig() {
  agentsLoading.value = true
  try {
    const [all, proj] = await Promise.all([
      listAvailableAgents(),
      listProjectAgents(projectId.value),
    ])
    availableAgents.value = all
    projectAgents.value = proj
    const enabled = proj.filter((a) => a.is_enabled)
    enabledAgentIds.value = enabled.map((a) => a.agent_id)
    const dir = proj.find((a) => a.is_director)
    directorAgentId.value = dir?.agent_id || null
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    agentsLoading.value = false
  }
}

function toggleAgent(id: number) {
  const idx = enabledAgentIds.value.indexOf(id)
  if (idx >= 0) {
    enabledAgentIds.value.splice(idx, 1)
  } else {
    enabledAgentIds.value.push(id)
  }
}

function isAgentEnabled(id: number) {
  return enabledAgentIds.value.includes(id)
}

function setDirector(id: number) {
  directorAgentId.value = id
  // 总控自动启用
  if (!isAgentEnabled(id)) {
    enabledAgentIds.value.push(id)
  }
}

const canProceedToIdea = computed(() => {
  // 必须有总控智能体 + 至少启用 1 个创作/文字类智能体
  if (!directorAgentId.value) return false
  const creativeAgents = availableAgents.value.filter(
    (a) => a.category === '文字' || a.category === '创作' || a.category === '视觉',
  )
  const hasCreative = creativeAgents.some((a) => isAgentEnabled(a.id))
  return hasCreative
})

async function saveAgentConfigAndContinue() {
  if (!directorAgentId.value) {
    ElMessage.warning('请选择一个总控智能体')
    return
  }
  if (!canProceedToIdea.value) {
    ElMessage.warning('请至少启用一个创作类智能体')
    return
  }
  savingAgents.value = true
  try {
    await setupProjectAgents(projectId.value, {
      director_agent_id: directorAgentId.value,
      enabled_agent_ids: enabledAgentIds.value,
    })
    ElMessage.success('智能体配置已保存')
    activeStep.value = 'idea'
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    savingAgents.value = false
  }
}

// 核心创作智能体（快速配置区域展示的）
const coreAgentKeys = ['director', 'screenwriter', 'storyboard', 'character_designer', 'copywriter']
const coreAgents = computed(() =>
  availableAgents.value.filter((a) => coreAgentKeys.includes(a.agent_key)),
)

// ── Step 1: 创意输入 ───────────────────────────────────────────────
const ideaForm = ref({
  idea: '',
  genre: '都市',
  style: '',
  total_episodes: 24,
})

const genreOptions = [
  '都市', '重生', '穿越', '甜宠', '仙侠', '古装',
  '悬疑', '校园', '职场', '家庭', '科幻', '喜剧',
]

// Step 2: 大纲
const episodes = ref<ScriptEpisode[]>([])

// Step 3: 人物
const characters = ref<ScriptCharacter[]>([])

// ── 计算 ──────────────────────────────────────────────────
const currentStepIndex = computed(() =>
  steps.findIndex((s) => s.key === activeStep.value),
)

// ── 数据加载 ──────────────────────────────────────────────
async function loadScript() {
  loading.value = true
  try {
    const res = await listScripts(projectId.value, { page: 1, page_size: 5 })
    if (res.items.length > 0) {
      scriptId.value = res.items[0].id
      const detail = await getScript(scriptId.value)
      script.value = detail
      // 已进入创作阶段的，跳过智能体配置
      if (detail.generation_stage !== 'idea') {
        activeStep.value = detail.generation_stage === 'completed'
          ? 'episodes'
          : detail.generation_stage as WizardStep
      }
      ideaForm.value = {
        idea: detail.core_idea || '',
        genre: detail.genre || '都市',
        style: detail.style || '',
        total_episodes: detail.total_episodes || 24,
      }
      // Load episodes
      if (detail.generation_stage !== 'idea') {
        const eps = await listEpisodes(detail.id)
        episodes.value = eps
      }
      if (detail.generation_stage === 'characters' || detail.generation_stage === 'episodes' || detail.generation_stage === 'completed') {
        const chars = await listCharacters(detail.id)
        characters.value = chars
      }
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

// ── Step 1 → Step 2: 生成大纲 ────────────────────────────
async function generateOutlineStep() {
  if (ideaForm.value.idea.trim().length < 5) {
    ElMessage.warning('请输入创意描述（至少5个字符）')
    return
  }
  generating.value = true
  try {
    let sid = scriptId.value
    // 如果没有剧本，先创建一个
    if (!sid) {
      const s = await createScript({
        project_id: projectId.value,
        title: ideaForm.value.idea.slice(0, 20) + '...',
        genre: ideaForm.value.genre,
        style: ideaForm.value.style || null,
        total_episodes: ideaForm.value.total_episodes,
      } as { project_id: number; title: string })
      sid = s.id
      scriptId.value = sid
    } else {
      await updateScript(sid, {
        genre: ideaForm.value.genre,
        style: ideaForm.value.style || null,
        total_episodes: ideaForm.value.total_episodes,
        core_idea: ideaForm.value.idea,
      })
    }

    // 生成大纲
    const result = await generateOutline(sid, {
      idea: ideaForm.value.idea,
      genre: ideaForm.value.genre,
      style: ideaForm.value.style || undefined,
      total_episodes: ideaForm.value.total_episodes,
    })
    script.value = result

    // 加载分集列表
    const eps = await listEpisodes(sid)
    episodes.value = eps

    activeStep.value = 'outline'
    ElMessage.success('大纲生成成功！')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    generating.value = false
  }
}

// ── Step 2 → Step 3: 生成人物 ────────────────────────────
async function generateCharactersStep() {
  if (!scriptId.value) return
  generating.value = true
  try {
    const chars = await generateCharacters(scriptId.value, { num_characters: 5 })
    characters.value = chars
    activeStep.value = 'characters'
    ElMessage.success('人物设定生成成功！')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    generating.value = false
  }
}

// ── Step 3 → Step 4: 进入逐集 ────────────────────────────
function goToEpisodes() {
  activeStep.value = 'episodes'
}

async function handleEpisodeClick(ep: (typeof episodes.value)[number]) {
  if (ep.is_generated) {
    router.push(`/projects/${projectId.value}/script`)
    return
  }
  generating.value = true
  try {
    if (!scriptId.value) return
    await generateEpisodeScript(scriptId.value, ep.episode_number)
    const eps = await listEpisodes(scriptId.value)
    episodes.value = eps
    ElMessage.success(`第${ep.episode_number}集剧本生成成功！`)
    router.push(`/projects/${projectId.value}/script`)
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    generating.value = false
  }
}

// 导入相关
const importVisible = ref('')
const importMode = ref<'text' | 'file'>('text')
const importType = ref<'auto' | 'novel' | 'fountain'>('auto')
const importText = ref('')
const importFile = ref<File | null>(null)
const importing = ref(false)
const importStats = ref<{ format: string; scenes: number; dialogues: number; characters: number } | null>(null)

async function doImport() {
  if (!script.value) return
  importing.value = true
  importStats.value = null
  try {
    let result
    if (importMode.value === 'text') {
      if (!importText.value.trim()) {
        ElMessage.warning('请输入要导入的文本')
        return
      }
      result = await importScriptText(script.value.id, importText.value, importType.value)
    } else {
      if (!importFile.value) {
        ElMessage.warning('请选择要导入的文件')
        return
      }
      result = await importScriptFile(script.value.id, importFile.value, importType.value)
    }
    importStats.value = result
    ElMessage.success(`导入成功！${result.scenes}个场景、${result.dialogues}段对白`)
    await loadScript()
    activeStep.value = 'episodes'
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    importing.value = false
  }
}

function handleFileChange(file: any) {
  importFile.value = file.raw
}

// ── 步骤切换 ──────────────────────────────────────────────
function goToStep(index: number) {
  const target = steps[index]
  // 只能跳到已完成或当前步骤
  const currentIdx = currentStepIndex.value
  if (index <= currentIdx) {
    activeStep.value = target.key
  }
}

function goPrev() {
  if (currentStepIndex.value > 0) {
    activeStep.value = steps[currentStepIndex.value - 1].key
  }
}

onMounted(() => {
  loadAgentConfig()
  loadScript()
})
</script>

<template>
  <div v-loading="loading" class="script-wizard">
    <!-- 步骤条 -->
    <div class="wizard-steps">
      <el-steps :active="currentStepIndex + 1" finish-status="success" align-center>
        <el-step
          v-for="(step, idx) in steps"
          :key="step.key"
          :title="step.label"
          @click.native="goToStep(idx)"
        >
          <template #icon>
            <el-icon :size="18"><component :is="step.icon" /></el-icon>
          </template>
        </el-step>
      </el-steps>
    </div>

    <!-- Step 0: 智能体配置 -->
    <div v-show="activeStep === 'agents'" class="wizard-content">
      <div class="step-card">
        <h3>配置智能体团队</h3>
        <p class="step-tip">选择总控智能体和参与创作的子智能体，AI 将协同完成短剧制作</p>

        <div class="agent-section" v-loading="agentsLoading">
          <h4 class="section-title">总控智能体</h4>
          <div class="agent-grid single">
            <div
              v-for="agent in availableAgents.filter(a => a.agent_key === 'director')"
              :key="agent.id"
              class="agent-select-card"
              :class="{ selected: directorAgentId === agent.id }"
              @click="setDirector(agent.id)"
            >
              <div class="agent-icon" :style="{ background: '#e6a23c' }">🎬</div>
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-desc">{{ agent.description }}</div>
              </div>
              <el-radio :model-value="directorAgentId === agent.id" @click.stop="setDirector(agent.id)">
                设为总控
              </el-radio>
            </div>
          </div>

          <h4 class="section-title">创作智能体</h4>
          <div class="agent-grid">
            <div
              v-for="agent in coreAgents.filter(a => a.agent_key !== 'director')"
              :key="agent.id"
              class="agent-select-card"
              :class="{ selected: isAgentEnabled(agent.id) }"
              @click="toggleAgent(agent.id)"
            >
              <div class="agent-icon">
                {{ agent.name?.[0] || '?' }}
              </div>
              <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-desc">{{ agent.description }}</div>
              </div>
              <el-checkbox :model-value="isAgentEnabled(agent.id)" @click.stop="toggleAgent(agent.id)" />
            </div>
          </div>
        </div>

        <div class="step-actions">
          <el-button
            type="primary"
            :icon="Check"
            :loading="savingAgents"
            :disabled="!canProceedToIdea"
            @click="saveAgentConfigAndContinue"
          >
            确认配置，开始创作
          </el-button>
        </div>
        <div v-if="!canProceedToIdea && availableAgents.length" class="config-hint">
          <el-icon><Setting /></el-icon>
          请选择总控智能体并至少启用一个创作智能体
        </div>
      </div>
    </div>

    <!-- Step 1: 创意输入 -->
    <div v-show="activeStep === 'idea'" class="wizard-content">
      <div class="step-card">
        <h3>创意输入</h3>

        <el-form label-width="80px" class="idea-form">
          <el-form-item label="创意" required>
            <el-input
              v-model="ideaForm.idea"
              type="textarea"
              :rows="3"
              placeholder="描述你的短剧创意..."
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-row :gutter="12">
            <el-col :span="8">
              <el-form-item label="题材">
                <el-select v-model="ideaForm.genre" style="width: 100%" placeholder="请选择">
                  <el-option v-for="g in genreOptions" :key="g" :label="g" :value="g" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="集数">
                <el-input-number v-model="ideaForm.total_episodes" :min="1" :max="200" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="风格">
                <el-input v-model="ideaForm.style" placeholder="如：轻松幽默" />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <div class="step-actions">
          <el-button
            type="primary"
            :icon="MagicStick"
            :loading="generating"
            :disabled="ideaForm.idea.trim().length < 5"
            @click="generateOutlineStep"
          >
            生成大纲
          </el-button>
        </div>

        <el-collapse v-model="importVisible" class="import-collapse">
          <el-collapse-item name="import" title="📄 导入剧本 / 小说">
            <p class="import-hint">
              粘贴或上传文本，自动识别格式并解析场景、角色、对白
            </p>

            <div class="import-toolbar">
              <el-radio-group v-model="importMode" size="small">
                <el-radio-button value="text">粘贴文本</el-radio-button>
                <el-radio-button value="file">上传文件</el-radio-button>
              </el-radio-group>
              <el-select v-model="importType" style="width: 140px; margin-left: 12px" size="default">
                <el-option label="自动识别" value="auto" />
                <el-option label="小说" value="novel" />
                <el-option label="Fountain" value="fountain" />
              </el-select>
            </div>

            <div v-show="importMode === 'text'" style="margin-top: 12px">
              <el-input
                v-model="importText"
                type="textarea"
                :rows="6"
                placeholder="粘贴小说或剧本内容..."
                class="import-textarea"
              />
            </div>

            <div v-show="importMode === 'file'" style="margin-top: 16px">
              <el-upload
                drag
                :auto-upload="false"
                :limit="1"
                accept=".txt,.fountain,.md"
                :on-change="handleFileChange"
                class="import-upload"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文件到这里，或 <em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    支持 .txt / .fountain 文件，单文件不超过 10MB
                  </div>
                </template>
              </el-upload>
            </div>

            <div class="step-actions">
              <el-button
                type="success"
                :icon="Upload"
               
                :loading="importing"
                @click="doImport"
              >
                开始导入
              </el-button>
            </div>

            <el-result
              v-if="importStats"
              icon="success"
              title="导入完成"
              :sub-title="`识别格式：${importStats.format}，创建 ${importStats.scenes} 个场景、${importStats.dialogues} 段对白、${importStats.characters} 个角色`"
            />
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <!-- Step 2: 故事大纲 -->
    <div v-show="activeStep === 'outline'" class="wizard-content">
      <div class="step-card">
        <h3>故事大纲</h3>

        <div class="outline-meta" v-if="script">
          <el-tag type="primary">{{ script.genre }}</el-tag>
          <el-tag type="info" effect="plain" v-if="script.style">{{ script.style }}</el-tag>
          <el-tag type="success" effect="plain">{{ episodes.length }} 集</el-tag>
        </div>

        <div class="synopsis-box" v-if="script?.synopsis">
          <div class="synopsis-label">故事梗概</div>
          <div class="synopsis-text">{{ script.synopsis }}</div>
        </div>

        <div class="episode-list">
          <div class="episode-item" v-for="ep in episodes" :key="ep.id">
            <div class="episode-number">第{{ ep.episode_number }}集</div>
            <div class="episode-info">
              <div class="episode-title">{{ ep.title || `第${ep.episode_number}集` }}</div>
              <div class="episode-synopsis">
                {{ ep.synopsis || '点击编辑分集梗概...' }}
              </div>
            </div>
            <el-tag v-if="ep.is_generated" size="small" type="success">已生成</el-tag>
            <el-tag v-else size="small" type="info" effect="plain">待生成</el-tag>
          </div>
        </div>

        <div class="step-actions">
          <el-button :icon="ArrowLeft" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="MagicStick"
           
            :loading="generating"
            @click="generateCharactersStep"
          >
            下一步：生成人物设定
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 3: 人物设定 -->
    <div v-show="activeStep === 'characters'" class="wizard-content">
      <div class="step-card">
        <h3>人物设定</h3>

        <div class="character-grid">
          <div class="character-card" v-for="char in characters" :key="char.id">
            <div class="char-avatar">
              {{ char.name?.[0] || '?' }}
            </div>
            <div class="char-info">
              <div class="char-header">
                <h4>{{ char.name }}</h4>
                <el-tag size="small" :type="char.character_type === '主角' ? 'danger' : 'info'">
                  {{ char.character_type }}
                </el-tag>
              </div>
              <p class="char-desc">{{ char.description || '暂无描述' }}</p>
              <div class="char-meta" v-if="char.age">
                <el-tag size="small" effect="plain">年龄：{{ char.age }}</el-tag>
              </div>
            </div>
          </div>
        </div>

        <div v-if="characters.length === 0" class="empty-tip">
          暂无人物数据
        </div>

        <div class="step-actions">
          <el-button :icon="ArrowLeft" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="VideoPlay"
           
            :disabled="characters.length === 0"
            @click="goToEpisodes"
          >
            下一步：逐集剧本
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 4: 逐集剧本 -->
    <div v-show="activeStep === 'episodes'" class="wizard-content">
      <div class="step-card">
        <h3>逐集剧本</h3>

        <div class="episode-grid">
          <div
            v-for="ep in episodes"
            :key="ep.id"
            class="episode-card"
            :class="{ generated: ep.is_generated }"
            @click="handleEpisodeClick(ep)"
          >
            <div class="ep-number">{{ ep.episode_number }}</div>
            <div class="ep-title">{{ ep.title || `第${ep.episode_number}集` }}</div>
            <div class="ep-status">
              <el-icon v-if="ep.is_generated" color="#67c23a"><Check /></el-icon>
              <span :class="ep.is_generated ? 'done' : 'pending'">
                {{ ep.is_generated ? '已生成' : '待生成' }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="episodes.length === 0" class="empty-tip">
          请先回到「故事大纲」步骤生成分集
        </div>

        <div class="step-actions">
          <el-button :icon="ArrowLeft" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="VideoPlay"
           
            @click="$router.push(`/projects/${projectId}/script`)"
          >
            打开剧本编辑器
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.script-wizard {
  padding: 12px 24px 20px 24px;
  min-height: 400px;
}

.wizard-steps {
  margin-bottom: 16px;
  padding: 12px 40px 4px 40px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}

.wizard-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-card {
  max-width: 850px;
  margin: 0 auto;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 20px 28px;
  border: 1px solid var(--el-border-color-lighter);
}

.step-card h3 {
  margin: 0 0 12px 0;
  font-size: 17px;
  font-weight: 600;
}

.step-tip {
  margin: 0 0 20px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.config-hint {
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: var(--el-text-color-placeholder);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.agent-section {
  margin-bottom: 16px;
}

.section-title {
  margin: 20px 0 10px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.agent-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.agent-grid.single {
  grid-template-columns: 1fr;
}

.agent-select-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--el-bg-color);
}

.agent-select-card:hover {
  border-color: var(--el-color-primary-light-5);
  background: var(--el-color-primary-light-9);
}

.agent-select-card.selected {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.agent-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
  min-width: 0;
}

.agent-info .agent-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 2px;
}

.agent-info .agent-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.idea-form {
  max-width: 700px;
}

.outline-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.synopsis-box {
  background: var(--el-fill-color-light);
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.synopsis-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.synopsis-text {
  font-size: 14px;
  line-height: 1.8;
  color: var(--el-text-color-primary);
  white-space: pre-wrap;
}

.episode-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
  max-height: 320px;
  overflow-y: auto;
}

.episode-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 6px;
  transition: all 0.2s;
}

.episode-item:hover {
  background: var(--el-fill-color-light);
}

.episode-number {
  font-weight: 600;
  color: var(--el-color-primary);
  font-size: 13px;
  width: 70px;
  flex-shrink: 0;
}

.episode-info {
  flex: 1;
  min-width: 0;
}

.episode-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 2px;
}

.episode-synopsis {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.character-card {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  transition: all 0.2s;
}

.character-card:hover {
  background: var(--el-fill-color-light);
}

.char-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--el-color-primary-light-3), var(--el-color-primary));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 600;
  flex-shrink: 0;
}

.char-info {
  flex: 1;
  min-width: 0;
}

.char-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.char-header h4 {
  margin: 0;
  font-size: 15px;
}

.char-desc {
  margin: 0 0 6px 0;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.char-meta {
  display: flex;
  gap: 4px;
}

.episode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.episode-card {
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  padding: 20px 16px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.episode-card:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-color-primary-light-5);
  transform: translateY(-2px);
}

.episode-card.generated {
  border-color: var(--el-color-success-light-5);
}

.ep-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary);
  margin-bottom: 4px;
}

.episode-card.generated .ep-number {
  color: var(--el-color-success);
}

.ep-title {
  font-size: 13px;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ep-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
}

.ep-status .done {
  color: var(--el-color-success);
}

.ep-status .pending {
  color: var(--el-text-color-secondary);
}

.step-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 12px;
  margin-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.empty-tip {
  text-align: center;
  padding: 40px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  margin-bottom: 24px;
}

.import-collapse {
  margin-top: 8px;
}

.import-hint {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.import-toolbar {
  display: flex;
  align-items: center;
}

.import-textarea :deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.import-upload {
  width: 100%;
}
</style>
