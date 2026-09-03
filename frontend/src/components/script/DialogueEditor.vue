<script setup lang="ts">
import { Plus, Delete, Edit, Check, Close } from '@element-plus/icons-vue'
import { ref, watch } from 'vue'
import type { Emotion, ScriptDialogue, ScriptDialogueUpdate } from '../../api/types'

const props = defineProps<{
  dialogues: ScriptDialogue[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'add'): void
  (e: 'update', id: number, payload: ScriptDialogueUpdate): void
  (e: 'delete', dialogue: ScriptDialogue): void
}>()

const editingId = ref<number | null>(null)
const editForm = ref({
  character_name: '',
  dialogue: '',
  action: '',
  emotion: '正常' as Emotion,
})

const emotionOptions: Emotion[] = [
  '正常', '开心', '悲伤', '愤怒', '惊讶', '恐惧',
  '紧张', '平静', '兴奋', '自信', '讽刺', '冷漠', '温柔',
]

watch(
  () => props.dialogues,
  () => {
    editingId.value = null
  },
)

function startEdit(dlg: ScriptDialogue) {
  editingId.value = dlg.id
  editForm.value = {
    character_name: dlg.character_name,
    dialogue: dlg.dialogue,
    action: dlg.action || '',
    emotion: dlg.emotion,
  }
}

function saveEdit() {
  if (editingId.value == null) return
  const payload: ScriptDialogueUpdate = {
    character_name: editForm.value.character_name,
    dialogue: editForm.value.dialogue,
    action: editForm.value.action || null,
    emotion: editForm.value.emotion,
  }
  emit('update', editingId.value, payload)
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
}

const emotionColorMap: Record<Emotion, string> = {
  '正常': '#909399',
  '开心': '#67c23a',
  '悲伤': '#909399',
  '愤怒': '#f56c6c',
  '惊讶': '#e6a23c',
  '恐惧': '#909399',
  '紧张': '#e6a23c',
  '平静': '#409eff',
  '兴奋': '#f56c6c',
  '自信': '#409eff',
  '讽刺': '#909399',
  '冷漠': '#909399',
  '温柔': '#f98fa7',
}
</script>

<template>
  <div class="dialogue-editor">
    <div class="dialogue-header">
      <span class="label">对白</span>
      <el-button type="primary" :icon="Plus" size="small" @click="$emit('add')">
        添加对白
      </el-button>
    </div>

    <div class="dialogue-list" v-loading="loading">
      <el-empty
        v-if="dialogues.length === 0"
        description="暂无对白，点击上方添加"
        :image-size="50"
      />

      <div
        v-for="(dlg, idx) in dialogues"
        :key="dlg.id"
        class="dialogue-item"
        :class="{ editing: editingId === dlg.id }"
      >
        <!-- View mode -->
        <template v-if="editingId !== dlg.id">
          <div class="dlg-header">
            <span class="dlg-index">{{ idx + 1 }}</span>
            <span class="dlg-character">{{ dlg.character_name }}</span>
            <el-tag
              size="small"
              :color="emotionColorMap[dlg.emotion] + '20'"
              :style="{ color: emotionColorMap[dlg.emotion], border: 'none' }"
            >
              {{ dlg.emotion }}
            </el-tag>
            <div class="dlg-actions">
              <el-button link :icon="Edit" @click="startEdit(dlg)">编辑</el-button>
              <el-button type="danger" link :icon="Delete" @click="$emit('delete', dlg)">
                删除
              </el-button>
            </div>
          </div>
          <div class="dlg-action" v-if="dlg.action">（{{ dlg.action }}）</div>
          <div class="dlg-text">{{ dlg.dialogue }}</div>
        </template>

        <!-- Edit mode -->
        <template v-else>
          <div class="dlg-edit-form">
            <div class="edit-row">
              <el-input
                v-model="editForm.character_name"
                placeholder="角色名"
                size="small"
                style="width: 120px"
              />
              <el-select v-model="editForm.emotion" size="small" style="width: 100px">
                <el-option
                  v-for="em in emotionOptions"
                  :key="em"
                  :label="em"
                  :value="em"
                />
              </el-select>
            </div>
            <el-input
              v-model="editForm.action"
              placeholder="动作提示（括号内）"
              size="small"
              class="edit-action"
            />
            <el-input
              v-model="editForm.dialogue"
              type="textarea"
              :rows="2"
              placeholder="台词内容"
            />
            <div class="edit-actions">
              <el-button size="small" :icon="Close" @click="cancelEdit">取消</el-button>
              <el-button type="primary" size="small" :icon="Check" @click="saveEdit">
                保存
              </el-button>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dialogue-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.dialogue-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 12px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.dialogue-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.dialogue-item {
  padding: 10px 12px;
  margin-bottom: 10px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.dialogue-item:hover {
  border-color: #dcdfe6;
  background: #f5f7fa;
}

.dialogue-item.editing {
  background: #ecf5ff;
  border-color: #409eff;
}

.dlg-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.dlg-index {
  font-size: 12px;
  color: #c0c4cc;
  width: 20px;
}

.dlg-character {
  font-weight: 600;
  font-size: 13px;
  color: #409eff;
}

.dlg-actions {
  margin-left: auto;
  display: none;
}

.dialogue-item:hover .dlg-actions {
  display: flex;
}

.dlg-action {
  font-size: 12px;
  color: #909399;
  font-style: italic;
  margin-bottom: 4px;
  padding-left: 28px;
}

.dlg-text {
  font-size: 14px;
  color: #303133;
  line-height: 1.7;
  padding-left: 28px;
  white-space: pre-wrap;
  word-break: break-word;
}

.dlg-edit-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.edit-row {
  display: flex;
  gap: 8px;
}

.edit-action {
  width: 100%;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
