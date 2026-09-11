<script setup lang="ts">
import { Connection, Delete, Edit, Plus, Refresh, View } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type TabPaneName } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { errorMessage } from '../api/client'
import {
  createMcp,
  deleteMcp,
  listMcps,
  refreshMcpTools,
  testExistingMcp,
  testMcpConnection,
  updateMcp,
} from '../api/mcps'
import type { Mcp, McpTestResult } from '../api/types'

const loading = ref(false)
const mcps = ref<Mcp[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const activeTab = ref<string>('basic')

// 筛选
const filterType = ref<string>('all')
const filterEnabled = ref<string>('all')
const searchKeyword = ref('')

// 测试连接
const testingConnection = ref(false)
const testResult = ref<McpTestResult | null>(null)

// 工具列表抽屉
const toolsDrawerVisible = ref(false)
const currentMcp = ref<Mcp | null>(null)
const toolsLoading = ref(false)
const tools = ref<Array<Record<string, unknown>>>([])

const typeOptions = [
  { label: '官方', value: 'official', type: 'success' },
  { label: '第三方', value: 'third_party', type: 'warning' },
  { label: '自定义', value: 'custom', type: 'info' },
]

const typeTagMap: Record<string, string> = {
  official: 'success',
  third_party: 'warning',
  custom: 'info',
}

const typeLabelMap: Record<string, string> = {
  official: '官方',
  third_party: '第三方',
  custom: '自定义',
}

const form = reactive({
  name: '',
  url: '',
  transport: 'streamable_http',
  mcp_type: 'custom',
  description: '',
  is_enabled: true,
  apiKey: '',
  apiKeyHeader: 'x-api-key',
  apiKeyPrefix: 'none',
  bearerToken: '',
  customHeaders: '',
  timeout: 10,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入服务地址', trigger: 'blur' }],
}

function getSecretsFromForm(): Record<string, unknown> | null {
  const secrets: Record<string, unknown> = {}
  if (form.apiKey) {
    secrets.api_key = form.apiKey
    secrets.api_key_header = form.apiKeyHeader
    secrets.api_key_prefix = form.apiKeyPrefix
  }
  if (form.bearerToken) {
    secrets.bearer_token = form.bearerToken
  }
  return Object.keys(secrets).length > 0 ? secrets : null
}

function getConfigFromForm(): Record<string, unknown> | null {
  const config: Record<string, unknown> = {}
  if (form.customHeaders) {
    try {
      const parsed = JSON.parse(form.customHeaders)
      config.headers = parsed
    } catch {
      // ignore parse errors, let validation fail elsewhere if needed
    }
  }
  if (form.timeout) {
    config.timeout = form.timeout
  }
  return Object.keys(config).length > 0 ? config : null
}

async function load() {
  loading.value = true
  try {
    const result = await listMcps({
      page: 1,
      page_size: 100,
      is_enabled: filterEnabled.value === 'all' ? undefined : filterEnabled.value === 'true',
      mcp_type: filterType.value === 'all' ? undefined : filterType.value,
      search: searchKeyword.value || undefined,
    })
    mcps.value = result.items
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    name: '',
    url: '',
    transport: 'streamable_http',
    mcp_type: 'custom',
    description: '',
    is_enabled: true,
    apiKey: '',
    apiKeyHeader: 'x-api-key',
    apiKeyPrefix: 'none',
    bearerToken: '',
    customHeaders: '',
    timeout: 10,
  })
  testResult.value = null
  activeTab.value = 'basic'
}

function openCreate() {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(mcp: Mcp) {
  editingId.value = mcp.id
  Object.assign(form, {
    name: mcp.name,
    url: mcp.url,
    transport: mcp.transport,
    mcp_type: mcp.mcp_type,
    description: mcp.description ?? '',
    is_enabled: mcp.is_enabled,
    apiKey: '',
    apiKeyHeader: 'x-api-key',
    apiKeyPrefix: 'none',
    bearerToken: '',
    customHeaders: mcp.config?.headers ? JSON.stringify(mcp.config.headers, null, 2) : '',
    timeout: (mcp.config as { timeout?: number })?.timeout ?? 10,
  })
  testResult.value = null
  activeTab.value = 'basic'
  dialogVisible.value = true
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = {
      name: form.name,
      url: form.url,
      transport: form.transport,
      mcp_type: form.mcp_type,
      description: form.description || null,
      is_enabled: form.is_enabled,
      config: getConfigFromForm(),
      secrets: getSecretsFromForm(),
    }
    if (editingId.value == null) {
      await createMcp(payload)
      ElMessage.success('MCP 创建成功')
    } else {
      await updateMcp(editingId.value, payload)
      ElMessage.success('MCP 更新成功')
    }
    dialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    saving.value = false
  }
}

async function testConnection() {
  if (!form.url) {
    ElMessage.warning('请先输入服务地址')
    return
  }
  testingConnection.value = true
  testResult.value = null
  try {
    testResult.value = await testMcpConnection({
      url: form.url,
      transport: form.transport,
      config: getConfigFromForm(),
      secrets: getSecretsFromForm(),
    })
    if (testResult.value.ok) {
      ElMessage.success(`连接成功，发现 ${testResult.value.tools?.length || 0} 个工具`)
    } else {
      ElMessage.error(`连接失败: ${testResult.value.error}`)
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    testingConnection.value = false
  }
}

async function testExisting(mcp: Mcp) {
  try {
    const result = await testExistingMcp(mcp.id)
    if (result.ok) {
      ElMessage.success(`连接成功，${result.latency_ms}ms，${result.tools?.length || 0} 个工具`)
    } else {
      ElMessage.error(`连接失败: ${result.error}`)
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function toggleEnabled(mcp: Mcp) {
  try {
    await updateMcp(mcp.id, { is_enabled: mcp.is_enabled })
  } catch (err) {
    mcp.is_enabled = !mcp.is_enabled
    ElMessage.error(errorMessage(err))
  }
}

async function remove(mcp: Mcp) {
  try {
    await ElMessageBox.confirm(`确定删除 MCP「${mcp.name}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteMcp(mcp.id)
    ElMessage.success('已删除')
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function openTools(mcp: Mcp) {
  currentMcp.value = mcp
  toolsDrawerVisible.value = true
  tools.value = mcp.tools || []
  if (!mcp.tools || mcp.tools.length === 0) {
    await refreshTools()
  }
}

async function refreshTools() {
  if (!currentMcp.value) return
  toolsLoading.value = true
  try {
    const result = await refreshMcpTools(currentMcp.value.id)
    tools.value = result.tools
    // 同步更新列表里的数据
    const idx = mcps.value.findIndex((m) => m.id === currentMcp.value!.id)
    if (idx >= 0) {
      mcps.value[idx].tools = result.tools
    }
    ElMessage.success(`刷新成功，共 ${result.count} 个工具`)
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    toolsLoading.value = false
  }
}

function handleTabChange(_name: TabPaneName) {
  // noop
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>MCP 管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建 MCP</el-button>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-bar">
      <div class="filter-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索名称或描述"
          clearable
          style="width: 240px"
          @input="load"
        />
        <el-select v-model="filterType" style="width: 140px" @change="load">
          <el-option label="全部分类" value="all" />
          <el-option label="官方" value="official" />
          <el-option label="第三方" value="third_party" />
          <el-option label="自定义" value="custom" />
        </el-select>
        <el-select v-model="filterEnabled" style="width: 120px" @change="load">
          <el-option label="全部状态" value="all" />
          <el-option label="已启用" value="true" />
          <el-option label="已禁用" value="false" />
        </el-select>
      </div>
    </el-card>

    <el-card shadow="never">
      <el-table :data="mcps" v-loading="loading" empty-text="暂无 MCP">
        <el-table-column prop="name" label="名称" min-width="140">
          <template #default="{ row }">
            <div class="mcp-name-cell">
              <span class="mcp-name">{{ row.name }}</span>
              <el-tag size="small" :type="typeTagMap[row.mcp_type] || 'info'">
                {{ typeLabelMap[row.mcp_type] || row.mcp_type }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="url" label="服务地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="transport" label="传输方式" width="130" />
        <el-table-column label="工具数" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.tools !== null">{{ row.tools?.length || 0 }}</span>
            <span v-else style="color: var(--el-text-color-placeholder)">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="启用" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_enabled" @change="toggleEnabled(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Connection" @click="testExisting(row)">测试</el-button>
            <el-button link type="primary" :icon="View" @click="openTools(row)">工具</el-button>
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId == null ? '新建 MCP' : '编辑 MCP'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="基础信息" name="basic">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
            <el-form-item label="名称" prop="name">
              <el-input v-model="form.name" maxlength="100" placeholder="给 MCP 起个名字" />
            </el-form-item>
            <el-form-item label="服务地址" prop="url">
              <el-input v-model="form.url" placeholder="https://..." maxlength="500" />
            </el-form-item>
            <el-form-item label="传输方式">
              <el-select v-model="form.transport" style="width: 100%">
                <el-option label="streamable_http" value="streamable_http" />
                <el-option label="sse" value="sse" />
                <el-option label="stdio" value="stdio" />
              </el-select>
            </el-form-item>
            <el-form-item label="类型">
              <el-select v-model="form.mcp_type" style="width: 100%">
                <el-option v-for="t in typeOptions" :key="t.value" :label="t.label" :value="t.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" />
            </el-form-item>
            <el-form-item label="启用">
              <el-switch v-model="form.is_enabled" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="鉴权配置" name="auth">
          <el-form label-width="120px">
            <el-divider content-position="left">API Key</el-divider>
            <el-form-item label="API Key">
              <el-input
                v-model="form.apiKey"
                type="password"
                show-password
                placeholder="输入 API Key，留空则不使用"
              />
            </el-form-item>
            <el-form-item label="Header 名称">
              <el-input v-model="form.apiKeyHeader" placeholder="x-api-key" />
            </el-form-item>
            <el-form-item label="前缀">
              <el-select v-model="form.apiKeyPrefix" style="width: 100%">
                <el-option label="无（直接使用值）" value="none" />
                <el-option label="Bearer" value="bearer" />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">Bearer Token</el-divider>
            <el-form-item label="Bearer Token">
              <el-input
                v-model="form.bearerToken"
                type="password"
                show-password
                placeholder="输入 Bearer Token，留空则不使用"
              />
            </el-form-item>

            <el-divider content-position="left">自定义 Headers</el-divider>
            <el-form-item label="Headers (JSON)">
              <el-input
                v-model="form.customHeaders"
                type="textarea"
                :rows="4"
                placeholder='{ "Authorization": "Bearer xxx" }'
                class="code-input"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="测试连接" name="test">
          <div class="test-panel">
            <el-button
              type="primary"
              :icon="Connection"
              :loading="testingConnection"
              @click="testConnection"
            >
              测试连接
            </el-button>
            <span class="test-tip">输入地址和鉴权信息后，测试是否能连通 MCP 服务</span>

            <div v-if="testResult" class="test-result" :class="{ ok: testResult.ok, fail: !testResult.ok }">
              <div class="test-status">
                <el-icon v-if="testResult.ok" :size="20" color="#67c23a">
                  <circle-check />
                </el-icon>
                <el-icon v-else :size="20" color="#f56c6c">
                  <circle-close />
                </el-icon>
                <span>{{ testResult.ok ? '连接成功' : '连接失败' }}</span>
              </div>
              <div v-if="testResult.latency_ms !== undefined" class="test-latency">
                延迟: {{ testResult.latency_ms }}ms
              </div>
              <div v-if="testResult.tools" class="test-tools">
                发现 {{ testResult.tools.length }} 个工具
              </div>
              <div v-if="testResult.error" class="test-error">
                错误: {{ testResult.error }}
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 工具列表抽屉 -->
    <el-drawer
      v-model="toolsDrawerVisible"
      :title="currentMcp ? `${currentMcp.name} - 工具列表` : '工具列表'"
      size="480px"
    >
      <template #header>
        <div class="drawer-header">
          <span>{{ currentMcp?.name }} - 工具列表</span>
          <el-button :icon="Refresh" size="small" :loading="toolsLoading" @click="refreshTools">
            刷新
          </el-button>
        </div>
      </template>

      <div v-loading="toolsLoading" class="tools-list">
        <el-empty v-if="!tools.length" description="暂无工具" />
        <div v-for="tool in tools" :key="(tool as { name: string }).name" class="tool-item">
          <div class="tool-name">{{ tool.name }}</div>
          <div class="tool-desc">{{ (tool as { description?: string }).description || '无描述' }}</div>
          <div v-if="(tool as { input_schema?: Record<string, unknown> }).input_schema" class="tool-schema">
            <el-collapse>
              <el-collapse-item title="参数结构" name="schema">
                <pre>{{ JSON.stringify((tool as { input_schema: Record<string, unknown> }).input_schema, null, 2) }}</pre>
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.filter-bar {
  margin-bottom: 12px;
}

.filter-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.mcp-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mcp-name {
  font-weight: 500;
}

.test-panel {
  padding: 8px 0;
}

.test-tip {
  margin-left: 12px;
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.test-result {
  margin-top: 16px;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid var(--el-border-color-lighter);
}

.test-result.ok {
  background: var(--el-color-success-light-9);
  border-color: var(--el-color-success-light-5);
}

.test-result.fail {
  background: var(--el-color-danger-light-9);
  border-color: var(--el-color-danger-light-5);
}

.test-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  margin-bottom: 8px;
}

.test-latency,
.test-tools,
.test-error {
  font-size: 13px;
  margin-top: 4px;
}

.test-error {
  color: var(--el-color-danger);
  font-family: monospace;
  word-break: break-all;
}

.code-input :deep(.el-textarea__inner) {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.tools-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-item {
  padding: 12px 14px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.tool-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-color-primary);
  margin-bottom: 4px;
}

.tool-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.tool-schema {
  margin-top: 8px;
}

.tool-schema pre {
  margin: 0;
  padding: 10px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 12px;
  font-family: Consolas, Monaco, monospace;
  overflow-x: auto;
  max-height: 300px;
}
</style>
