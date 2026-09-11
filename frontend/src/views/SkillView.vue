<script setup lang="ts">
import { Delete, Edit, Plus, Upload, DocumentCopy } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { errorMessage } from '../api/client'
import {
  createSkill,
  deleteSkill,
  importSkillFromFile,
  importSkillFromText,
  listSkills,
  updateSkill,
} from '../api/skills'
import type { Skill, SkillImportResult } from '../api/types'

const loading = ref(false)
const skills = ref<Skill[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()

// 导入对话框
const importDialogVisible = ref(false)
const importTab = ref<'text' | 'file'>('text')
const importing = ref(false)
const importText = ref('')
const importName = ref('')
const importDescription = ref('')
const importOverwrite = ref(false)
const importResult = ref<SkillImportResult | null>(null)
const fileInputRef = ref()

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

// ── 导入功能 ─────────────────────────────────────────────

function openImport() {
  importTab.value = 'text'
  importText.value = ''
  importName.value = ''
  importDescription.value = ''
  importOverwrite.value = false
  importResult.value = null
  importDialogVisible.value = true
}

async function doImportText() {
  if (!importText.value.trim()) {
    ElMessage.warning('请输入 Skill 内容')
    return
  }
  importing.value = true
  importResult.value = null
  try {
    const result = await importSkillFromText({
      text: importText.value,
      name: importName.value || undefined,
      description: importDescription.value || undefined,
      overwrite: importOverwrite.value,
    })
    importResult.value = result
    showImportResult(result)
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    importing.value = false
  }
}

async function handleFileChange(uploadFile: UploadFile) {
  const file = uploadFile.raw
  if (!file) return
  importing.value = true
  importResult.value = null
  try {
    const result = await importSkillFromFile(file, importOverwrite.value)
    importResult.value = result
    showImportResult(result)
    await load()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    importing.value = false
    // 重置文件选择
    if (fileInputRef.value) {
      fileInputRef.value.clearFiles()
    }
  }
}

function showImportResult(result: SkillImportResult) {
  const parts: string[] = []
  if (result.created > 0) parts.push(`新建 ${result.created} 个`)
  if (result.updated > 0) parts.push(`更新 ${result.updated} 个`)
  if (result.skipped > 0) parts.push(`跳过 ${result.skipped} 个`)
  const msg = `导入完成：${parts.join('，')}`
  if (result.errors.length > 0 && result.created === 0 && result.updated === 0) {
    ElMessage.error(msg)
  } else if (result.errors.length > 0) {
    ElMessage.warning(msg + '，部分失败')
  } else {
    ElMessage.success(msg)
  }
}

function getResultTagType(key: string) {
  if (key === 'created') return 'success'
  if (key === 'updated') return 'warning'
  if (key === 'skipped') return 'info'
  if (key === 'errors') return 'danger'
  return 'info'
}

onMounted(load)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>Skill 管理</h2>
      <div class="header-actions">
        <el-button :icon="Upload" @click="openImport">导入 Skill</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建 Skill</el-button>
      </div>
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

    <!-- 新建/编辑对话框 -->
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

    <!-- 导入对话框 -->
    <el-dialog v-model="importDialogVisible" title="导入 Skill" width="600px" :close-on-click-modal="false">
      <el-tabs v-model="importTab">
        <!-- 文本粘贴导入 -->
        <el-tab-pane label="粘贴文本" name="text">
          <el-form label-width="100px">
            <el-form-item label="名称">
              <el-input v-model="importName" placeholder="留空则自动从文本中识别" maxlength="100" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="importDescription" placeholder="留空则自动从文本中识别" maxlength="500" />
            </el-form-item>
            <el-form-item label="Skill 内容" required>
              <el-input
                v-model="importText"
                type="textarea"
                :rows="10"
                placeholder="粘贴 Skill 内容&#10;&#10;支持格式：&#10;1. Markdown 格式：# Skill 名称 + 描述 + 内容&#10;2. YAML front matter：--- name: xxx --- + 内容&#10;3. 纯文本：第一行为名称，其余为内容"
                class="code-input"
              />
            </el-form-item>
            <el-form-item label="覆盖同名">
              <el-switch v-model="importOverwrite" />
              <span class="form-hint">开启后，同名 Skill 会被覆盖更新</span>
            </el-form-item>
          </el-form>
          <div class="import-actions">
            <el-button type="primary" :icon="DocumentCopy" :loading="importing" @click="doImportText">
              导入
            </el-button>
          </div>
        </el-tab-pane>

        <!-- 文件导入 -->
        <el-tab-pane label="上传文件" name="file">
          <el-form label-width="100px">
            <el-form-item label="选择文件">
              <el-upload
                ref="fileInputRef"
                :auto-upload="false"
                :show-file-list="false"
                accept=".md,.txt,.json"
                :on-change="handleFileChange"
              >
                <el-button :icon="Upload" :loading="importing">选择文件</el-button>
                <span class="form-hint" style="margin-left: 10px">支持 .md / .txt / .json</span>
              </el-upload>
            </el-form-item>
            <el-form-item label="文件说明">
              <div class="file-tips">
                <p><strong>.md / .txt</strong>：单个 Skill，自动识别名称和描述</p>
                <p><strong>.json</strong>：批量导入，格式为 Skill 对象数组</p>
              </div>
            </el-form-item>
            <el-form-item label="覆盖同名">
              <el-switch v-model="importOverwrite" />
              <span class="form-hint">开启后，同名 Skill 会被覆盖更新</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <!-- 导入结果 -->
      <div v-if="importResult" class="import-result">
        <el-divider>导入结果</el-divider>
        <div class="result-stats">
          <el-tag :type="getResultTagType('total')">总数: {{ importResult.total }}</el-tag>
          <el-tag type="success">新建: {{ importResult.created }}</el-tag>
          <el-tag type="warning">更新: {{ importResult.updated }}</el-tag>
          <el-tag type="info">跳过: {{ importResult.skipped }}</el-tag>
        </div>
        <div v-if="importResult.errors.length > 0" class="result-errors">
          <div class="errors-title">错误 / 警告 ({{ importResult.errors.length }})</div>
          <ul>
            <li v-for="(err, idx) in importResult.errors" :key="idx">{{ err }}</li>
          </ul>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.header-actions {
  display: flex;
  gap: 8px;
}

.code-input :deep(.el-textarea__inner) {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  line-height: 1.6;
}

.form-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-left: 4px;
}

.import-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.file-tips {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.8;
}

.file-tips p {
  margin: 0;
}

.import-result {
  margin-top: 8px;
}

.result-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.result-errors {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 10px 12px;
}

.errors-title {
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 6px;
  color: var(--el-color-danger);
}

.result-errors ul {
  margin: 0;
  padding-left: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  max-height: 150px;
  overflow-y: auto;
}

.result-errors li {
  margin-bottom: 2px;
}
</style>
