<script setup lang="ts">
import { computed } from 'vue'
import type { ScriptDetail } from '../../api/types'

const props = defineProps<{
  script: ScriptDetail | null
  loading?: boolean
}>()

/**
 * 生成 Fountain 格式的预览文本
 * 纯前端渲染，与后端 export_fountain 逻辑保持一致
 */
const fountainText = computed(() => {
  if (!props.script) return ''
  const lines: string[] = []

  // Title page
  lines.push(`Title: ${props.script.title}`)
  if (props.script.logline) lines.push(`Logline: ${props.script.logline}`)
  if (props.script.genre) lines.push(`Genre: ${props.script.genre}`)
  if (props.script.style) lines.push(`Style: ${props.script.style}`)
  lines.push(`Version: ${props.script.version}`)
  lines.push('')

  // Synopsis
  if (props.script.synopsis) {
    lines.push('= 故事大纲')
    lines.push('')
    props.script.synopsis.trim().split('\n').forEach((para) => {
      const p = para.trim()
      if (p) {
        lines.push(p)
        lines.push('')
      }
    })
  }

  // Scenes
  props.script.scenes?.forEach((scene) => {
    const slug = `${scene.int_ext}. ${scene.location.toUpperCase()} - ${scene.time_of_day}`
    lines.push(slug)
    lines.push('')

    if (scene.description) {
      scene.description.trim().split('\n').forEach((para) => {
        const p = para.trim()
        if (p) {
          lines.push(p)
          lines.push('')
        }
      })
    }

    scene.dialogues?.forEach((dlg) => {
      if (dlg.action) {
        lines.push(`(${dlg.action})`)
      }
      lines.push(dlg.character_name.toUpperCase())
      dlg.dialogue.trim().split('\n').forEach((para) => {
        const p = para.trim()
        if (p) lines.push(p)
      })
      lines.push('')
    })

    lines.push('')
  })

  return lines.join('\n')
})
</script>

<template>
  <div class="script-preview" v-loading="loading">
    <div class="preview-header">
      <span>剧本预览 (Fountain 格式)</span>
    </div>
    <div class="preview-content">
      <el-empty v-if="!script" description="选择剧本或场景后预览" :image-size="60" />
      <pre v-else class="fountain-text">{{ fountainText }}</pre>
    </div>
  </div>
</template>

<style scoped>
.script-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #ebeef5;
  background: #fafafa;
}

.preview-header {
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  background: #f5f7fa;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.fountain-text {
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>