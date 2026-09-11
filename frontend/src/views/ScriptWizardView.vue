<script setup lang="ts">
import { ArrowLeft, Check, MagicStick, Notebook, User, VideoPlay } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorMessage } from '../api/client'
import { createScript, generateCharacters, generateOutline, getScript, listCharacters, listEpisodes, listScripts, updateScript } from '../api/scripts'
import type {
  ScriptDetail,
  ScriptCharacter,
  ScriptEpisode,
  ScriptGenerationStage,
} from '../api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.projectId))

// ── 四步配置 ──────────────────────────────────────────────
const steps = [
  { key: 'idea', label: '创意输入', icon: Notebook, desc: '描述你的短剧创意' },
  { key: 'outline', label: '故事大纲', icon: MagicStick, desc: '生成故事大纲与分集' },
  { key: 'characters', label: '人物设定', icon: User, desc: '设计主要人物档案' },
  { key: 'episodes', label: '逐集剧本', icon: VideoPlay, desc: '生成每集详细剧本' },
] as const

const activeStep = ref<ScriptGenerationStage>('idea')
const script = ref<ScriptDetail | null>(null)
const scriptId = ref<number | null>(null)
const loading = ref(false)
const generating = ref(false)

// Step 1: 创意输入
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
      activeStep.value = detail.generation_stage === 'completed'
        ? 'episodes'
        : detail.generation_stage
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

function openEpisodeEditor(_episodeId: number) {
  router.push(`/projects/${projectId.value}/script`)
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

onMounted(loadScript)
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
          :description="step.desc"
          @click.native="goToStep(idx)"
        >
          <template #icon>
            <el-icon :size="20"><component :is="step.icon" /></el-icon>
          </template>
        </el-step>
      </el-steps>
    </div>

    <!-- Step 1: 创意输入 -->
    <div v-show="activeStep === 'idea'" class="wizard-content">
      <div class="step-card">
        <h3>描述你的短剧创意</h3>
        <p class="step-desc">告诉 AI 你想做什么样的短剧，它会帮你生成完整的故事大纲。</p>

        <el-form label-width="100px" class="idea-form">
          <el-form-item label="创意描述" required>
            <el-input
              v-model="ideaForm.idea"
              type="textarea"
              :rows="5"
              placeholder="例如：一个重生回到高中的女孩，决定改变命运，却意外发现了当年被掩盖的真相..."
              maxlength="500"
              show-word-limit
            />
          </el-form-item>

          <el-row :gutter="16">
            <el-col :span="8">
              <el-form-item label="题材">
                <el-select v-model="ideaForm.genre" style="width: 100%" placeholder="选择题材">
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
            size="large"
            :loading="generating"
            :disabled="ideaForm.idea.trim().length < 5"
            @click="generateOutlineStep"
          >
            下一步：生成故事大纲
          </el-button>
        </div>
      </div>
    </div>

    <!-- Step 2: 故事大纲 -->
    <div v-show="activeStep === 'outline'" class="wizard-content">
      <div class="step-card">
        <h3>故事大纲与分集梗概</h3>
        <p class="step-desc">AI 为你生成了整体故事架构，你可以调整每一集的概要。</p>

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
          <el-button :icon="ArrowLeft" size="large" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="MagicStick"
            size="large"
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
        <h3>主要人物档案</h3>
        <p class="step-desc">以下是根据故事大纲生成的主要角色，你可以编辑调整。</p>

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
          <el-button :icon="ArrowLeft" size="large" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="VideoPlay"
            size="large"
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
        <h3>逐集剧本制作</h3>
        <p class="step-desc">选择一集开始详细剧本创作，进入专业编辑器进行精修。</p>

        <div class="episode-grid">
          <div
            v-for="ep in episodes"
            :key="ep.id"
            class="episode-card"
            :class="{ generated: ep.is_generated }"
            @click="openEpisodeEditor(ep.id)"
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
          <el-button :icon="ArrowLeft" size="large" @click="goPrev">上一步</el-button>
          <el-button
            type="primary"
            :icon="VideoPlay"
            size="large"
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
  padding: 20px 24px;
  min-height: 500px;
}

.wizard-steps {
  margin-bottom: 24px;
  padding: 20px 40px;
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
  max-width: 900px;
  margin: 0 auto;
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 32px 40px;
  border: 1px solid var(--el-border-color-lighter);
}

.step-card h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
}

.step-desc {
  margin: 0 0 24px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.idea-form {
  max-width: 700px;
}

.outline-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.synopsis-box {
  background: var(--el-fill-color-light);
  padding: 16px;
  border-radius: 6px;
  margin-bottom: 20px;
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
  gap: 16px;
  padding-top: 16px;
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
</style>
