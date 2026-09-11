<script setup lang="ts">
import { Edit, MagicStick, Refresh, Setting, Star, Switch } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { errorMessage } from '../api/client'
import {
  listAvailableAgents,
  listProjectAgents,
  setupProjectAgents,
  toggleProjectAgent,
  updateProjectAgent,
} from '../api/projectAgents'
import type { AgentSimple, ProjectAgentConfig } from '../api/types'

const route = useRoute()
const projectId = computed(() => Number(route.params.projectId))

const loading = ref(false)
const saving = ref(false)
const availableAgents = ref<AgentSimple[]>([])
const projectAgents = ref<ProjectAgentConfig[]>([])

// 编辑配置的弹窗
const editDialogVisible = ref(false)
const editingAgent = ref<ProjectAgentConfig | null>(null)
const editForm = ref({
  priority: 100,
  temperature: 0.7,
  role_description: '',
})

// 分类
const agentCategories = computed(() => {
  const cats = new Map<string, AgentSimple[]>()
  for (const a of availableAgents.value) {
    const cat = a.category || '其他'
    if (!cats.has(cat)) cats.set(cat, [])
    cats.get(cat)!.push(a)
  }
  return cats
})

// 分类列表（按顺序展示）
const categoryList = computed(() => {
  const entries = Array.from(agentCategories.value.entries())
  return entries
})

const director = computed(() =>
  projectAgents.value.find((a) => a.is_director),
)

const enabledCount = computed(() =>
  projectAgents.value.filter((a) => a.is_enabled).length,
)

// ── 数据加载 ──────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const [all, project] = await Promise.all([
      listAvailableAgents(),
      listProjectAgents(projectId.value),
    ])
    availableAgents.value = all
    projectAgents.value = project
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

// 获取 agent 的配置，没有则返回默认值
function getAgentConfig(agentId: number): ProjectAgentConfig | undefined {
  return projectAgents.value.find((c) => c.agent_id === agentId)
}

function isAgentEnabled(agentId: number): boolean {
  const cfg = getAgentConfig(agentId)
  return cfg?.is_enabled ?? false
}

function isDirector(agentId: number): boolean {
  const cfg = getAgentConfig(agentId)
  return cfg?.is_director ?? false
}

// ── 操作 ──────────────────────────────────────────────────
async function handleToggle(agent: AgentSimple) {
  try {
    await toggleProjectAgent(projectId.value, agent.id)
    await loadData()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function setAsDirector(agent: AgentSimple) {
  try {
    // 先确保这个 agent 已启用
    const cfg = getAgentConfig(agent.id)
    if (!cfg || !cfg.is_enabled) {
      await setupProjectAgents(projectId.value, {
        director_agent_id: agent.id,
        enabled_agent_ids: [
          ...projectAgents.value.filter((a) => a.is_enabled).map((a) => a.agent_id),
          agent.id,
        ],
      })
    } else {
      await updateProjectAgent(projectId.value, agent.id, { is_director: true })
    }
    await loadData()
    ElMessage.success(`已将「${agent.name}」设为总控智能体`)
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

function openEdit(agent: AgentSimple) {
  const cfg = getAgentConfig(agent.id)
  editingAgent.value = cfg || null
  editForm.value = {
    priority: cfg?.priority ?? 100,
    temperature: cfg?.temperature ?? agent.temperature,
    role_description: cfg?.role_description || '',
  }
  editDialogVisible.value = true
}

async function saveEdit() {
  if (!editingAgent.value) return
  saving.value = true
  try {
    await updateProjectAgent(projectId.value, editingAgent.value.agent_id, {
      priority: editForm.value.priority,
      temperature: editForm.value.temperature,
      role_description: editForm.value.role_description,
    })
    ElMessage.success('配置已保存')
    editDialogVisible.value = false
    await loadData()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    saving.value = false
  }
}

// 快速配置：一键推荐配置
async function applyRecommended() {
  try {
    // 推荐配置：director 总控 + 核心创作智能体
    const coreKeys = ['director', 'screenwriter', 'storyboard', 'character_designer', 'copywriter']
    const coreIds = availableAgents.value
      .filter((a) => coreKeys.includes(a.agent_key))
      .map((a) => a.id)

    const directorAgent = availableAgents.value.find((a) => a.agent_key === 'director')
    if (!directorAgent) {
      ElMessage.warning('未找到总控智能体')
      return
    }

    await setupProjectAgents(projectId.value, {
      director_agent_id: directorAgent.id,
      enabled_agent_ids: coreIds,
    })
    await loadData()
    ElMessage.success('已应用推荐配置')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

onMounted(loadData)
</script>

<template>
  <div v-loading="loading" class="agent-config">
    <!-- 头部 -->
    <div class="config-header">
      <div>
        <h3><el-icon :size="20" color="#409eff"><Setting /></el-icon> 项目智能体配置</h3>
        <p class="subtitle">
          选择参与本项目的智能体，设置总控智能体统筹全流程
        </p>
      </div>
      <div class="header-actions">
        <el-button :icon="MagicStick" @click="applyRecommended">
          应用推荐配置
        </el-button>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>
    </div>

    <!-- 总控状态条 -->
    <div class="director-bar" v-if="director">
      <div class="director-info">
        <el-icon :size="24" color="#e6a23c"><Star /></el-icon>
        <div>
          <div class="director-label">总控智能体</div>
          <div class="director-name">{{ director.agent_name }}</div>
        </div>
      </div>
      <div class="director-stats">
        <el-tag type="success" effect="plain">
          已启用 {{ enabledCount }} 个智能体
        </el-tag>
      </div>
    </div>
    <div class="director-bar empty" v-else>
      <el-icon :size="24" color="#909399"><Star /></el-icon>
      <span>尚未设置总控智能体，选择一个智能体作为项目总指挥</span>
    </div>

    <!-- 智能体列表（按分类） -->
    <div class="agent-category" v-for="[cat, agents] in categoryList" :key="cat">
      <h4 class="category-title">{{ cat }}</h4>
      <div class="agent-list">
        <div
          v-for="agent in agents"
          :key="agent.id"
          class="agent-card"
          :class="{
            enabled: isAgentEnabled(agent.id),
            director: isDirector(agent.id),
          }"
        >
          <div class="agent-header">
            <div class="agent-title">
              <span class="agent-name">{{ agent.name }}</span>
              <el-tag size="small" effect="plain" v-if="isDirector(agent.id)" type="warning">
                总控
              </el-tag>
            </div>
            <el-switch
              :model-value="isAgentEnabled(agent.id)"
              :active-icon="Switch"
              @change="handleToggle(agent)"
            />
          </div>
          <div class="agent-desc">{{ agent.description || '暂无描述' }}</div>
          <div class="agent-meta">
            <el-tag size="small" effect="plain">{{ agent.agent_type }}</el-tag>
            <span class="temp">温度: {{ agent.temperature }}</span>
          </div>
          <div class="agent-actions" v-if="isAgentEnabled(agent.id)">
            <el-button
              size="small"
              type="warning"
              :icon="Star"
              plain
              :disabled="isDirector(agent.id)"
              @click="setAsDirector(agent)"
            >
              {{ isDirector(agent.id) ? '当前总控' : '设为总控' }}
            </el-button>
            <el-button
              size="small"
              :icon="Edit"
              @click="openEdit(agent)"
            >
              配置
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialogVisible" title="智能体配置" width="500px">
      <el-form label-width="100px" v-if="editingAgent">
        <el-form-item label="优先级">
          <el-input-number v-model="editForm.priority" :min="1" :max="1000" style="width: 100%" />
          <div class="form-hint">数字越小优先级越高（执行顺序越靠前）</div>
        </el-form-item>
        <el-form-item label="温度">
          <el-slider v-model="editForm.temperature" :min="0" :max="2" :step="0.1" />
          <div class="form-hint">
            0 = 精确严谨，1 = 平衡，>1 = 更有创造性
          </div>
        </el-form-item>
        <el-form-item label="角色描述">
          <el-input
            v-model="editForm.role_description"
            type="textarea"
            :rows="3"
            placeholder="该智能体在本项目中的具体角色和职责..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.agent-config {
  padding: 20px 24px;
  min-height: 500px;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.director-bar {
  background: linear-gradient(135deg, var(--el-color-warning-light-9), var(--el-color-warning-light-8));
  border: 1px solid var(--el-color-warning-light-5);
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.director-bar.empty {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color-lighter);
  color: var(--el-text-color-secondary);
  gap: 8px;
}

.director-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.director-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 2px;
}

.director-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.agent-category {
  margin-bottom: 24px;
}

.category-title {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-secondary);
  padding-left: 8px;
  border-left: 3px solid var(--el-color-primary);
}

.agent-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}

.agent-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.agent-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.agent-card.enabled {
  border-color: var(--el-color-success-light-5);
  background: var(--el-color-success-light-9);
}

.agent-card.director {
  border-color: var(--el-color-warning);
  box-shadow: 0 2px 12px rgba(230, 162, 60, 0.15);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.agent-name {
  font-size: 15px;
  font-weight: 600;
}

.agent-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
  min-height: 38px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.temp {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.agent-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.form-hint {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-top: 4px;
}
</style>
