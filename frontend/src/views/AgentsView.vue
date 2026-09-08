<script setup lang="ts">
import { Edit, Promotion } from '@element-plus/icons-vue'
import { ElMessage, type TableInstance } from 'element-plus'
import { computed, nextTick, onMounted, reactive, ref } from 'vue'

import {
  chatWithAgent,
  listAgentMetadata,
  setAgentEnabled,
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

    <el-dialog v-model="editDialogVisible" title="编辑智能体" width="620px">
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
</style>
