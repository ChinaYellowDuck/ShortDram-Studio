<script setup lang="ts">
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { errorMessage } from '../api/client'
import { createMcp, deleteMcp, listMcps, updateMcp } from '../api/mcps'
import type { Mcp } from '../api/types'

const loading = ref(false)
const mcps = ref<Mcp[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  url: '',
  transport: 'streamable_http',
  description: '',
  is_enabled: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  url: [{ required: true, message: '请输入服务地址', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const result = await listMcps({ page: 1, page_size: 100 })
    mcps.value = result.items
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    url: '',
    transport: 'streamable_http',
    description: '',
    is_enabled: true,
  })
  dialogVisible.value = true
}

function openEdit(mcp: Mcp) {
  editingId.value = mcp.id
  Object.assign(form, {
    name: mcp.name,
    url: mcp.url,
    transport: mcp.transport,
    description: mcp.description ?? '',
    is_enabled: mcp.is_enabled,
  })
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
      description: form.description || null,
      is_enabled: form.is_enabled,
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

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>MCP 管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建 MCP</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="mcps" v-loading="loading" empty-text="暂无 MCP">
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="url" label="服务地址" min-width="220" show-overflow-tooltip />
        <el-table-column prop="transport" label="传输方式" width="140" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="启用" width="80" align="center">
          <template #default="{ row }">
            <el-switch v-model="row.is_enabled" @change="toggleEnabled(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="openEdit(row)">编辑</el-button>
            <el-button link type="danger" :icon="Delete" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editingId == null ? '新建 MCP' : '编辑 MCP'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="100" />
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
        <el-form-item label="描述">
          <el-input v-model="form.description" maxlength="500" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
