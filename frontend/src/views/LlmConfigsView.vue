<script setup lang="ts">
import { Connection, Delete, Plus, Star } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { errorMessage } from '../api/client'
import {
  createConfig,
  deleteConfig,
  getProviders,
  listConfigs,
  setDefaultConfig,
  testConfig,
} from '../api/llm-configs'
import type { LLMConfig, LLMProvider } from '../api/types'

const loading = ref(false)
const configs = ref<LLMConfig[]>([])
const total = ref(0)
const providers = ref<LLMProvider[]>([])

const dialogVisible = ref(false)
const creating = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  provider: '',
  model_name: '',
  api_key: '',
  base_url: '',
  description: '',
  is_default: false,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入配置名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入 API Key', trigger: 'blur' }],
}

const selectedProvider = computed(() =>
  providers.value.find((p) => p.key === form.provider),
)

const testingIds = ref<Set<number>>(new Set())

async function load() {
  loading.value = true
  try {
    const [configsRes, providersRes] = await Promise.all([
      listConfigs({ page: 1, page_size: 100 }),
      getProviders(),
    ])
    configs.value = configsRes.items
    total.value = configsRes.total
    providers.value = providersRes
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

function onProviderChange() {
  const provider = selectedProvider.value
  if (provider) form.model_name = provider.default_model
}

async function submitCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  creating.value = true
  try {
    await createConfig({
      name: form.name,
      provider: form.provider,
      model_name: form.model_name,
      api_key: form.api_key,
      base_url: form.base_url || null,
      description: form.description || null,
      is_default: form.is_default,
    })
    ElMessage.success('LLM 配置创建成功')
    dialogVisible.value = false
    Object.assign(form, {
      name: '',
      provider: '',
      model_name: '',
      api_key: '',
      base_url: '',
      description: '',
      is_default: false,
    })
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    creating.value = false
  }
}

async function makeDefault(config: LLMConfig) {
  try {
    await setDefaultConfig(config.id)
    ElMessage.success(`已将「${config.name}」设为默认配置`)
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function test(config: LLMConfig) {
  testingIds.value.add(config.id)
  try {
    const result = await testConfig(config.id)
    if (result.success) {
      ElMessage.success(
        `连通性测试通过（${result.model ?? config.model_name}，${result.response_time_ms?.toFixed(0) ?? '-'}ms）`,
      )
    } else {
      ElMessage.error(`测试失败：${result.message}`)
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    testingIds.value.delete(config.id)
  }
}

async function remove(config: LLMConfig) {
  try {
    await ElMessageBox.confirm(`确定删除配置「${config.name}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteConfig(config.id)
    ElMessage.success('已删除')
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>LLM 配置</h2>
      <el-button type="primary" :icon="Plus" @click="dialogVisible = true">
        新建配置
      </el-button>
    </div>

    <el-alert
      type="info"
      :closable="false"
      title="智能体对话依赖默认 LLM 配置"
      description="创建配置后请将其设为默认，并可点击「测试」验证连通性。API Key 加密存储，不会在页面展示。"
      style="margin-bottom: 16px"
    />

    <el-card shadow="never">
      <el-table :data="configs" v-loading="loading" empty-text="暂无 LLM 配置">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="配置名称" min-width="160">
          <template #default="{ row }">
            {{ row.name }}
            <el-tag v-if="row.is_default" type="success" size="small" style="margin-left: 6px">
              默认
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="provider" label="提供商" width="120" />
        <el-table-column prop="model_name" label="模型" width="180" />
        <el-table-column prop="base_url" label="Base URL" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.base_url || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_default"
              link
              :icon="Star"
              @click="makeDefault(row)"
            >
              设默认
            </el-button>
            <el-button
              link
              type="primary"
              :icon="Connection"
              :loading="testingIds.has(row.id)"
              @click="test(row)"
            >
              测试
            </el-button>
            <el-button link type="danger" :icon="Delete" @click="remove(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建 LLM 配置" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="配置名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：DeepSeek 生产配置" maxlength="100" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select
            v-model="form.provider"
            placeholder="选择 LLM 提供商"
            style="width: 100%"
            @change="onProviderChange"
          >
            <el-option
              v-for="p in providers"
              :key="p.key"
              :label="p.name"
              :value="p.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称" prop="model_name">
          <el-input v-model="form.model_name" placeholder="例如：deepseek-chat" maxlength="100" />
        </el-form-item>
        <el-form-item label="API Key" prop="api_key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="sk-..."
          />
        </el-form-item>
        <el-form-item
          v-if="selectedProvider?.supports_base_url"
          label="Base URL"
        >
          <el-input v-model="form.base_url" placeholder="可选，自定义 API 地址" maxlength="500" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="可选" maxlength="500" />
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
