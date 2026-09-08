<script setup lang="ts">
import { Delete, Edit, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { errorMessage } from '../api/client'
import { createSkill, deleteSkill, listSkills, updateSkill } from '../api/skills'
import type { Skill } from '../api/types'

const loading = ref(false)
const skills = ref<Skill[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  content: '',
  is_enabled: true,
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  content: [{ required: true, message: '请输入指令内容', trigger: 'blur' }],
}

async function load() {
  loading.value = true
  try {
    const result = await listSkills({ page: 1, page_size: 100 })
    skills.value = result.items
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, { name: '', description: '', content: '', is_enabled: true })
  dialogVisible.value = true
}

function openEdit(skill: Skill) {
  editingId.value = skill.id
  Object.assign(form, {
    name: skill.name,
    description: skill.description ?? '',
    content: skill.content,
    is_enabled: skill.is_enabled,
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
      description: form.description || null,
      content: form.content,
      is_enabled: form.is_enabled,
    }
    if (editingId.value == null) {
      await createSkill(payload)
      ElMessage.success('Skill 创建成功')
    } else {
      await updateSkill(editingId.value, payload)
      ElMessage.success('Skill 更新成功')
    }
    dialogVisible.value = false
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    saving.value = false
  }
}

async function toggleEnabled(skill: Skill) {
  try {
    await updateSkill(skill.id, { is_enabled: skill.is_enabled })
  } catch (err) {
    skill.is_enabled = !skill.is_enabled
    ElMessage.error(errorMessage(err))
  }
}

async function remove(skill: Skill) {
  try {
    await ElMessageBox.confirm(`确定删除 Skill「${skill.name}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteSkill(skill.id)
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
      <h2>Skill 管理</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建 Skill</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="skills" v-loading="loading" empty-text="暂无 Skill">
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '-' }}</template>
        </el-table-column>
        <el-table-column prop="content" label="指令内容" min-width="240" show-overflow-tooltip />
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

    <el-dialog v-model="dialogVisible" :title="editingId == null ? '新建 Skill' : '编辑 Skill'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="100" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" maxlength="500" />
        </el-form-item>
        <el-form-item label="指令内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="5" placeholder="输入技能指令/提示词" />
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
