<script setup lang="ts">
import { Delete, Plus, Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { createProject, deleteProject, listProjects } from '../api/projects'
import { errorMessage } from '../api/client'
import type { Project, ProjectStatus } from '../api/types'

const loading = ref(false)
const projects = ref<Project[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')

const dialogVisible = ref(false)
const creating = ref(false)
const formRef = ref<FormInstance>()
const form = reactive({
  name: '',
  description: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

const statusMeta: Record<ProjectStatus, { label: string; type: 'info' | 'primary' | 'success' | 'warning' }> = {
  draft: { label: '草稿', type: 'info' },
  in_progress: { label: '制作中', type: 'primary' },
  completed: { label: '已完成', type: 'success' },
  archived: { label: '已归档', type: 'warning' },
}

async function load() {
  loading.value = true
  try {
    const res = await listProjects({
      page: page.value,
      page_size: pageSize.value,
      search: search.value || undefined,
    })
    projects.value = res.items
    total.value = res.total
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  creating.value = true
  try {
    await createProject({
      name: form.name,
      description: form.description || null,
    })
    ElMessage.success('项目创建成功')
    dialogVisible.value = false
    form.name = ''
    form.description = ''
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    creating.value = false
  }
}

async function remove(project: Project) {
  try {
    await ElMessageBox.confirm(`确定删除项目「${project.name}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteProject(project.id)
    ElMessage.success('已删除')
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>项目管理</h2>
      <el-space>
        <el-input
          v-model="search"
          placeholder="按名称搜索"
          clearable
          style="width: 220px"
          @keyup.enter="load()"
          @clear="load()"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" :icon="Plus" @click="dialogVisible = true">
          新建项目
        </el-button>
      </el-space>
    </div>

    <el-card shadow="never">
      <el-table :data="projects" v-loading="loading" empty-text="暂无项目，点击右上角创建">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="项目名称" min-width="180" />
        <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMeta[row.status as ProjectStatus].type" size="small">
              {{ statusMeta[row.status as ProjectStatus].label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button type="danger" link :icon="Delete" @click="remove(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > pageSize"
        style="margin-top: 16px; justify-content: flex-end"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        v-model:current-page="page"
        @current-change="load()"
      />
    </el-card>

    <el-dialog v-model="dialogVisible" title="新建短剧项目" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：重生之都市逆袭" maxlength="200" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="一句话描述你的短剧创意"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
