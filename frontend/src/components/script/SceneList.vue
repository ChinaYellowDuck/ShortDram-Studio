<script setup lang="ts">
import { Plus, Sort, Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import type { ScriptScene } from '../../api/types'

const props = defineProps<{
  scenes: ScriptScene[]
  activeSceneId: number | null
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', scene: ScriptScene): void
  (e: 'add'): void
  (e: 'delete', scene: ScriptScene): void
  (e: 'update-scene', scene: ScriptScene): void
}>()

function formatSceneTitle(scene: ScriptScene) {
  return `第 ${scene.scene_number} 场 · ${scene.location}`
}

function handleDelete(scene: ScriptScene, evt: Event) {
  evt.stopPropagation()
  ElMessageBox.confirm(`确定删除场景「${formatSceneTitle(scene)}」吗？`, '删除确认', {
    type: 'warning',
  })
    .then(() => emit('delete', scene))
    .catch(() => {})
}
</script>

<template>
  <div class="scene-list">
    <div class="list-header">
      <span class="scene-count">{{ scenes.length }} 场戏</span>
      <el-button type="primary" :icon="Plus" size="small" @click="$emit('add')">
        新增场景
      </el-button>
    </div>

    <div class="scene-items" v-loading="loading">
      <el-empty v-if="scenes.length === 0" description="暂无场景，点击上方新增" :image-size="60" />

      <div
        v-for="scene in scenes"
        :key="scene.id"
        class="scene-item"
        :class="{ active: scene.id === activeSceneId }"
        @click="emit('select', scene)"
      >
        <div class="scene-drag-handle">
          <el-icon><Sort /></el-icon>
        </div>
        <div class="scene-info">
          <div class="scene-title">{{ formatSceneTitle(scene) }}</div>
          <div class="scene-meta">
            <el-tag size="small" type="info">{{ scene.int_ext }}</el-tag>
            <el-tag size="small">{{ scene.time_of_day }}</el-tag>
            <span class="dialogue-count">{{ scene.dialogues?.length || 0 }} 句对白</span>
          </div>
          <div class="scene-desc" v-if="scene.description">
            {{ scene.description.slice(0, 60) }}{{ scene.description.length > 60 ? '...' : '' }}
          </div>
        </div>
        <div class="scene-actions">
          <el-button type="danger" link :icon="Delete" @click="handleDelete(scene, $event)" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scene-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
  background: #fafafa;
}

.scene-count {
  font-size: 13px;
  color: #909399;
}

.scene-items {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.scene-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  margin-bottom: 6px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.scene-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.scene-item.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.scene-drag-handle {
  color: #c0c4cc;
  padding-top: 2px;
  cursor: grab;
  flex-shrink: 0;
}

.scene-info {
  flex: 1;
  min-width: 0;
}

.scene-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 6px;
}

.scene-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.dialogue-count {
  font-size: 12px;
  color: #909399;
}

.scene-desc {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.scene-actions {
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
}

.scene-item:hover .scene-actions {
  opacity: 1;
}
</style>
