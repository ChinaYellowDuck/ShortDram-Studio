<script setup lang="ts">
import { Edit, Refresh, Promotion } from '@element-plus/icons-vue'
import { ElMessage, type TableInstance } from 'element-plus'
import { computed, nextTick, onMounted, reactive, ref } from 'vue'

import {
  chatWithAgent,
  listAgentMetadata,
  setAgentEnabled,
  listAgentMcpTools,
  updateAgentMetadata,
} from '../api/agents'
import { errorMessage } from '../api/client'
import { listConfigs } from '../api/llm-configs'
import { listMcps } from '../api/mcps'
import { listSkills } from '../api/skills'
import type { AgentMetadata, LLMConfig, Mcp, Skill } from '../api/types'

const loading = ref(false)
const agents = ref<AgentMetadata[]>([])
const textConfigs = ref<LLMConfig[]>([])
const mcps = ref<Mcp[]>([])
const skills = ref<Skill[]>([])
const savingIds = ref(new Set<number>())
const selectedAgentKey = ref('hello_agent')
const message = ref('')
const sending = ref(false)
const tableRef = ref<TableInstance>()
const editDialogVisible = ref(false)
const editingAgentId = ref<number | null>(null)
const editSaving = ref(false)
const editTab = ref('basic')
const agentTools = ref<Array<Record<string, unknown>>>([])
const toolsLoading = ref(false)

async function loadAgentTools() {
  if (!editingAgentId.value) return
  toolsLoading.value = true
  try {
    const result = await listAgentMcpTools(editingAgentId.value)
    agentTools.value = result.tools
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    toolsLoading.value = false
  }
}
const editForm = reactive({
  name: '',
  description: '',
  agent_type: '',
  category: '',
  temperature: 0.7,
  system_message: '',
  is_enabled: true,
  mcp_ids: [] as number[],
  skill_ids: [] as number[],
})

const selectedAgent = computed(() =>
  agents.value.find((agent) => agent.agent_key === selectedAgentKey.value),
)

interface ChatItem {
  role: 'user' | 'agent' | 'system'
  content: string
}
const chatHistory = ref<ChatItem[]>([])

async function load() {
  loading.value = true
  try {
    const [agentResult, configResult, mcpResult, skillResult] = await Promise.all([
      listAgentMetadata(),
      listConfigs({ page: 1, page_size: 100, model_type: 'text' }),
      listMcps({ page: 1, page_size: 100 }),
      listSkills({ page: 1, page_size: 100 }),
    ])
    agents.value = agentResult.items
    textConfigs.value = configResult.items
    mcps.value = mcpResult.items
    skills.value = skillResult.items
    if (!agents.value.some((agent) => agent.agent_key === selectedAgentKey.value && agent.is_enabled)) {
      const firstEnabled = agents.value.find((agent) => agent.is_enabled)
      selectedAgentKey.value = firstEnabled?.agent_key ?? 'hello_agent'
    }
    nextTick(() => {
      const current = agents.value.find((agent) => agent.agent_key === selectedAgentKey.value)
      if (current) tableRef.value?.setCurrentRow(current)
    })
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

async function toggleEnabled(agent: AgentMetadata) {
  savingIds.value.add(agent.id)
  try {
    await setAgentEnabled(agent.id, agent.is_enabled)
    ElMessage.success(agent.is_enabled ? '智能体已启用' : '智能体已禁用')
  } catch (err) {
    agent.is_enabled = !agent.is_enabled
    ElMessage.error(errorMessage(err))
  } finally {
    savingIds.value.delete(agent.id)
  }
}

async function changeDefaultLlm(agent: AgentMetadata) {
  savingIds.value.add(agent.id)
  try {
    await updateAgentMetadata(agent.id, {
      default_llm_config_id: agent.default_llm_config_id,
    })
    ElMessage.success('默认文字模型已更新')
  } catch (err) {
    ElMessage.error(errorMessage(err))
    await load()
  } finally {
    savingIds.value.delete(agent.id)
  }
}

function openEdit(agent: AgentMetadata) {
  editingAgentId.value = agent.id
  Object.assign(editForm, {
    name: agent.name,
    description: agent.description ?? '',
    agent_type: agent.agent_type,
    category: agent.category ?? '',
    temperature: agent.temperature,
    system_message: agent.system_message ?? '',
    is_enabled: agent.is_enabled,
    mcp_ids: [...agent.mcp_ids],
    skill_ids: [...agent.skill_ids],
  })
  editTab.value = 'basic'
  agentTools.value = []
  editDialogVisible.value = true
}

async function submitEdit() {
  if (editingAgentId.value == null) return
  editSaving.value = true
  try {
    await updateAgentMetadata(editingAgentId.value, {
      name: editForm.name,
      description: editForm.description || null,
      agent_type: editForm.agent_type,
      category: editForm.category || null,
      temperature: editForm.temperature,
      system_message: editForm.system_message || null,
      is_enabled: editForm.is_enabled,
      mcp_ids: editForm.mcp_ids,
      skill_ids: editForm.skill_ids,
    })
    ElMessage.success('智能体已更新')
    editDialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    editSaving.value = false
  }
}

async function send() {
  const text = message.value.trim()
  if (!text || sending.value) return
  chatHistory.value.push({ role: 'user', content: text })
  message.value = ''
  sending.value = true
  try {
    const res = await chatWithAgent(selectedAgentKey.value, text)
    chatHistory.value.push({
      role: 'agent',
      content: `${res.response}\n（${selectedAgent.value?.name ?? res.agent} · ${res.llm_config.provider} / ${res.llm_config.model} · 运行 #${res.run_id}）`,
    })
  } catch (err) {
    chatHistory.value.push({ role: 'system', content: `调用失败：${errorMessage(err)}` })
  } finally {
    sending.value = false
  }
}

function onSelectAgent(row: AgentMetadata | null) {
  if (!row) return
  if (!row.is_enabled) {
    ElMessage.warning('该智能体已禁用，无法对话测试')
    return
  }
  if (selectedAgentKey.value === row.agent_key) return
  selectedAgentKey.value = row.agent_key
  chatHistory.value = []
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header"><h2>智能体管理</h2></div>

    <el-card shadow="never" v-loading="loading">
      <el-table
        ref="tableRef"
        :data="agents"
        empty-text="暂无智能体"
        highlight-current-row
        row-key="id"
        @current-change="onSelectAgent"
      >
        <el-table-column prop="name" label="智能体" min-width="150">
          <template #default="{ row }">
            <div class="agent-name">{{ row.name }}</div>
            <div class="agent-key">{{ row.agent_key }} · v{{ row.version }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
        <el-table-column prop="agent_type" label="类型" width="100" />
        <el-table-column label="默认文字模型" min-width="220">
          <template #default="{ row }">
            <div @click.stop>
              <el-select
                v-model="row.default_llm_config_id"
                clearable
                placeholder="使用全局默认配置"
                :loading="savingIds.has(row.id)"
                @change="changeDefaultLlm(row)"
              >
                <el-option
                  v-for="config in textConfigs"
                  :key="config.id"
                  :label="`${config.name}（${config.model_name}）`"
                  :value="config.id"
                />
              </el-select>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="启用" width="90" align="center">
          <template #default="{ row }">
            <div @click.stop>
              <el-switch
                v-model="row.is_enabled"
                :loading="savingIds.has(row.id)"
                @change="toggleEnabled(row)"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <div @click.stop>
              <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" class="chat-card">
      <template #header>
        <div class="chat-header">
          <span>智能体对话测试</span>
          <el-tag v-if="selectedAgent" type="success" size="small">
            {{ selectedAgent.name }}
          </el-tag>
          <span class="chat-hint">点击上方表格中的智能体即可切换</span>
        </div>
      </template>
      <div class="chat-box">
        <el-empty v-if="chatHistory.length === 0" description="发送一条消息试试" :image-size="60" />
        <div v-for="(item, index) in chatHistory" :key="index" class="chat-item" :class="item.role">
          <div class="chat-bubble">{{ item.content }}</div>
        </div>
      </div>
      <div class="chat-input">
        <el-input v-model="message" placeholder="输入消息，回车发送" :disabled="sending" @keyup.enter="send()" />
        <el-button type="primary" :icon="Promotion" :loading="sending" @click="send()">发送</el-button>
      </div>
    </el-card>

    <el-dialog v-model="editDialogVisible" title="编辑智能体" width="640px">
      <el-tabs v-model="editTab">
        <el-tab-pane label="基础配置" name="basic">
          <el-form :model="editForm" label-width="100px">
            <el-form-item label="名称">
              <el-input v-model="editForm.name" maxlength="100" />
            </el-form-item>
            <el-form-item label="类型">
              <el-input v-model="editForm.agent_type" maxlength="50" />
            </el-form-item>
            <el-form-item label="分类">
              <el-input v-model="editForm.category" maxlength="50" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="editForm.description" type="textarea" :rows="2" maxlength="500" />
            </el-form-item>
            <el-form-item label="温度">
              <el-slider v-model="editForm.temperature" :min="0" :max="2" :step="0.1" show-input />
            </el-form-item>
            <el-form-item label="System 提示">
              <el-input v-model="editForm.system_message" type="textarea" :rows="3" placeholder="系统提示词（可选）" />
            </el-form-item>
            <el-form-item label="绑定 MCP">
              <el-select v-model="editForm.mcp_ids" multiple clearable style="width: 100%" placeholder="选择要绑定的 MCP">
                <el-option v-for="mcp in mcps" :key="mcp.id" :label="mcp.name" :value="mcp.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="绑定 Skill">
              <el-select v-model="editForm.skill_ids" multiple clearable style="width: 100%" placeholder="选择要绑定的 Skill">
                <el-option v-for="skill in skills" :key="skill.id" :label="skill.name" :value="skill.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="editForm.is_enabled" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="MCP 工具" name="mcp-tools">
          <div class="tools-panel">
            <div v-if="!editingAgentId" style="color: var(--el-text-color-secondary); text-align: center; padding: 20px 0;">
              请先保存智能体后再查看 MCP 工具
            </div>
            <div v-else>
              <div class="tools-header">
                <span class="tools-count">共 {{ agentTools.length }} 个可用工具</span>
                <el-button size="small" :icon="Refresh" :loading="toolsLoading" @click="loadAgentTools">
                  刷新
                </el-button>
              </div>
              <el-empty v-if="agentTools.length === 0 && !toolsLoading" description="暂无工具，请先绑定 MCP 并确保工具已缓存" />
              <div v-else class="tools-list">
                <div v-for="tool in agentTools" :key="(tool as { name: string }).name" class="tool-card">
                  <div class="tool-name">{{ (tool as { name: string }).name }}</div>
                  <div class="tool-server">
                    <el-tag size="small" type="info">{{ (tool as { mcp_server_name?: string }).mcp_server_name }}</el-tag>
                  </div>
                  <div class="tool-desc">{{ (tool as { description?: string }).description || '无描述' }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSaving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.agent-name { font-weight: 600; }
.agent-key, .chat-hint { color: #909399; font-size: 12px; }
.chat-header { display: flex; align-items: center; gap: 12px; }
.chat-hint { margin-left: 12px; font-weight: normal; }
.chat-card { margin-top: 16px; }
.chat-box { height: 280px; overflow-y: auto; padding: 8px; background: #fafafa; border-radius: 8px; }
.chat-item { display: flex; margin-bottom: 12px; }
.chat-item.user { justify-content: flex-end; }
.chat-item.agent { justify-content: flex-start; }
.chat-item.system { justify-content: center; }
.chat-bubble { max-width: 75%; padding: 8px 12px; border-radius: 8px; white-space: pre-wrap; word-break: break-word; font-size: 14px; }
.chat-item.user .chat-bubble { background: #409eff; color: #fff; }
.chat-item.agent .chat-bubble { background: #fff; border: 1px solid #ebeef5; }
.chat-item.system .chat-bubble { background: #fef0f0; color: #f56c6c; font-size: 12px; }
.chat-input { display: flex; gap: 8px; margin-top: 12px; }

.tools-panel {
  padding: 4px 0;
}

.tools-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.tools-count {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.tools-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  max-height: 360px;
  overflow-y: auto;
}

.tool-card {
  padding: 10px 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-bg-color);
}

.tool-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--el-color-primary);
  margin-bottom: 4px;
}

.tool-server {
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
