<script setup lang="ts">
import {
  ArrowLeft,
  Check,
  Download,
  Edit,
  MagicStick,
  View,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorMessage } from '../api/client'
import {
  createDialogue,
  createScene,
  createScript,
  deleteScene,
  exportFountain,
  generateScript,
  getScript,
  listScripts,
  refineScene,
  updateDialogue,
  updateScene,
  updateScript,
} from '../api/scripts'
import type {
  Emotion,
  IntExt,
  ScriptDialogue,
  ScriptDialogueUpdate,
  ScriptScene,
  ScriptSceneUpdate,
  ScriptUpdate,
  TimeOfDay,
} from '../api/types'

import DialogueEditor from '../components/script/DialogueEditor.vue'
import SceneList from '../components/script/SceneList.vue'
import ScriptPreview from '../components/script/ScriptPreview.vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.projectId))

// ── State ────────────────────────────────────────────────────────────────────

const loading = ref(false)
const scriptId = ref<number | null>(null)
const script = ref<any>(null)
const activeScene = ref<ScriptScene | null>(null)

const sceneLoading = ref(false)
const dialogueLoading = ref(false)

// ── Meta info edit ───────────────────────────────────────────────────────────

const editingMeta = ref(false)
const metaForm = ref({
  title: '',
  logline: '',
  genre: '',
  style: '',
  synopsis: '',
  total_episodes: 1,
})

// ── Scene edit ───────────────────────────────────────────────────────────────

const sceneFormVisible = ref(false)
const sceneForm = ref({
  scene_number: '',
  location: '',
  int_ext: 'INT' as IntExt,
  time_of_day: '日' as TimeOfDay,
  description: '',
})

// ── AI generation ────────────────────────────────────────────────────────────

const generateDialogVisible = ref(false)
const generating = ref(false)
const generateForm = ref({
  idea: '',
  genre: '都市',
  style: '',
  num_scenes: 10,
})

const refineDialogVisible = ref(false)
const refining = ref(false)
const refineFeedback = ref('')

// ── Fountain preview ────────────────────────────────────────────────────────

const previewVisible = ref(true)
const fountainExporting = ref(false)

// ── Loaders ──────────────────────────────────────────────────────────────────

async function loadScript() {
  loading.value = true
  try {
    // List scripts for this project
    const scripts = await listScripts(projectId.value, { page: 1, page_size: 10 })
    if (scripts.items.length > 0) {
      scriptId.value = scripts.items[0].id
      await loadScriptDetail(scripts.items[0].id)
    } else {
      script.value = null
      scriptId.value = null
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    loading.value = false
  }
}

async function loadScriptDetail(id: number) {
  try {
    const detail = await getScript(id)
    script.value = detail
    metaForm.value = {
      title: detail.title,
      logline: detail.logline || '',
      genre: detail.genre || '',
      style: detail.style || '',
      synopsis: detail.synopsis || '',
      total_episodes: detail.total_episodes,
    }
    if (detail.scenes?.length > 0) {
      activeScene.value = detail.scenes[0]
    } else {
      activeScene.value = null
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function selectScene(scene: ScriptScene) {
  activeScene.value = scene
}

// ── Meta info actions ───────────────────────────────────────────────────────

async function saveMeta() {
  if (!scriptId.value) return
  try {
    const payload: ScriptUpdate = {
      title: metaForm.value.title,
      logline: metaForm.value.logline || null,
      genre: metaForm.value.genre || null,
      style: metaForm.value.style || null,
      synopsis: metaForm.value.synopsis || null,
      total_episodes: metaForm.value.total_episodes,
    }
    await updateScript(scriptId.value, payload)
    script.value = { ...script.value, ...payload }
    editingMeta.value = false
    ElMessage.success('已保存')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

// ── Scene actions ───────────────────────────────────────────────────────────

function openAddScene() {
  sceneForm.value = {
    scene_number: String((script.value?.scenes?.length || 0) + 1),
    location: '',
    int_ext: 'INT',
    time_of_day: '日',
    description: '',
  }
  sceneFormVisible.value = true
}

async function submitScene() {
  if (!scriptId.value) return
  if (!sceneForm.value.location) {
    ElMessage.warning('请输入场景地点')
    return
  }
  sceneLoading.value = true
  try {
    const scene = await createScene(scriptId.value, {
      scene_number: sceneForm.value.scene_number,
      location: sceneForm.value.location,
      int_ext: sceneForm.value.int_ext,
      time_of_day: sceneForm.value.time_of_day,
      description: sceneForm.value.description || null,
    })
    // Reload to get updated list
    await loadScriptDetail(scriptId.value)
    activeScene.value = scene
    sceneFormVisible.value = false
    ElMessage.success('场景已添加')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    sceneLoading.value = false
  }
}

async function handleDeleteScene(scene: ScriptScene) {
  try {
    await deleteScene(scene.id)
    if (scriptId.value) {
      await loadScriptDetail(scriptId.value)
    }
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function handleUpdateSceneField(field: keyof ScriptSceneUpdate, value: any) {
  if (!activeScene.value) return
  const payload: ScriptSceneUpdate = { [field]: value }
  try {
    const updated = await updateScene(activeScene.value.id, payload)
    activeScene.value = updated
    // Also update in script.scenes
    if (script.value?.scenes) {
      const idx = script.value.scenes.findIndex((s: ScriptScene) => s.id === updated.id)
      if (idx >= 0) script.value.scenes[idx] = updated
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

// ── Dialogue actions ────────────────────────────────────────────────────────

async function handleAddDialogue() {
  if (!activeScene.value) return
  dialogueLoading.value = true
  try {
    await createDialogue(activeScene.value.id, {
      character_name: '新角色',
      dialogue: '',
      emotion: '正常',
    })
    // Reload scene
    const updated = await (await import('../api/scripts')).getScene(activeScene.value.id)
    activeScene.value = updated
    if (script.value?.scenes) {
      const idx = script.value.scenes.findIndex((s: ScriptScene) => s.id === updated.id)
      if (idx >= 0) script.value.scenes[idx] = updated
    }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    dialogueLoading.value = false
  }
}

async function handleUpdateDialogue(id: number, payload: ScriptDialogueUpdate) {
  if (!activeScene.value) return
  try {
    const updated = await updateDialogue(id, payload)
    // Update in active scene
    const dlgs = [...activeScene.value.dialogues]
    const idx = dlgs.findIndex((d) => d.id === id)
    if (idx >= 0) dlgs[idx] = updated
    activeScene.value = { ...activeScene.value, dialogues: dlgs }
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function handleDeleteDialogue(dlg: ScriptDialogue) {
  if (!activeScene.value) return
  try {
    await (await import('../api/scripts')).deleteDialogue(dlg.id)
    const dlgs = activeScene.value.dialogues.filter((d) => d.id !== dlg.id)
    activeScene.value = { ...activeScene.value, dialogues: dlgs }
    ElMessage.success('已删除')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

// ── AI Generation ───────────────────────────────────────────────────────────

function openGenerateDialog() {
  generateForm.value = {
    idea: '',
    genre: script.value?.genre || '都市',
    style: script.value?.style || '',
    num_scenes: 10,
  }
  generateDialogVisible.value = true
}

async function doGenerateScript() {
  if (!generateForm.value.idea.trim()) {
    ElMessage.warning('请输入创意描述')
    return
  }
  generating.value = true
  try {
    const result = await generateScript({
      idea: generateForm.value.idea,
      genre: generateForm.value.genre,
      style: generateForm.value.style || undefined,
      num_scenes: generateForm.value.num_scenes,
    })

    // Create or update script
    const r = result.result

    if (!scriptId.value) {
      const newScript = await createScript({
        project_id: projectId.value,
        title: generateForm.value.idea.slice(0, 30) + '...',
        logline: r.logline || null,
        genre: r.genre || null,
        style: r.style || null,
        synopsis: r.synopsis || null,
        total_episodes: 1,
      })
      scriptId.value = newScript.id
    } else {
      await updateScript(scriptId.value, {
        logline: r.logline || null,
        genre: r.genre || null,
        style: r.style || null,
        synopsis: r.synopsis || null,
      })
    }

    // Create characters
    const charMap: Record<string, number> = {}
    for (const char of r.characters || []) {
      try {
        const c = await (await import('../api/scripts')).createCharacter(scriptId.value, {
          name: char.name || '未知角色',
          description: char.description || null,
          character_type:
            char.role === '主角' || char.role === 'LEAD' ? '主角' : '配角',
          age: char.age || null,
          appearance: char.personality || char.appearance || null,
        })
        charMap[char.name] = c.id
      } catch {}
    }

    // Create scenes
    for (const sceneData of r.scenes || []) {
      try {
        const scene = await createScene(scriptId.value, {
          scene_number: String(sceneData.scene_number || ''),
          location: sceneData.location || '未知地点',
          int_ext: (sceneData.int_ext as IntExt) || 'INT',
          time_of_day: (sceneData.time_of_day as TimeOfDay) || '日',
          description: sceneData.description || null,
          order_index: sceneData.order_index || 0,
        })

        // Create dialogues
        for (const dlg of sceneData.dialogues || []) {
          try {
            await createDialogue(scene.id, {
              character_name: dlg.character_name || '旁白',
              dialogue: dlg.dialogue || '',
              action: dlg.action || null,
              emotion: (dlg.emotion as Emotion) || '正常',
              character_id: charMap[dlg.character_name] || null,
            })
          } catch {}
        }
      } catch {}
    }

    await loadScriptDetail(scriptId.value)
    generateDialogVisible.value = false
    ElMessage.success('剧本生成完成！')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    generating.value = false
  }
}

function openRefineDialog() {
  if (!activeScene.value) {
    ElMessage.warning('请先选择一个场景')
    return
  }
  refineFeedback.value = ''
  refineDialogVisible.value = true
}

async function doRefineScene() {
  if (!activeScene.value || !scriptId.value) return
  if (!refineFeedback.value.trim()) {
    ElMessage.warning('请输入修改意见')
    return
  }
  refining.value = true
  try {
    const result = await refineScene({
      script_id: scriptId.value,
      scene_id: activeScene.value.id,
      feedback: refineFeedback.value,
    })

    const refined = result.refined_scene
    // Update scene
    await updateScene(activeScene.value.id, {
      description: refined.description || null,
    })

    // Delete old dialogues and create new ones
    for (const dlg of activeScene.value.dialogues) {
      try {
        await (await import('../api/scripts')).deleteDialogue(dlg.id)
      } catch {}
    }

    for (const dlg of refined.dialogues || []) {
      try {
        await createDialogue(activeScene.value.id, {
          character_name: dlg.character_name,
          dialogue: dlg.dialogue,
          action: dlg.action || null,
          emotion: dlg.emotion || '正常',
        })
      } catch {}
    }

    // Reload
    const updated = await (await import('../api/scripts')).getScene(activeScene.value.id)
    activeScene.value = updated
    await loadScriptDetail(scriptId.value)

    refineDialogVisible.value = false
    ElMessage.success('场景打磨完成！')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    refining.value = false
  }
}

// ── Fountain export ─────────────────────────────────────────────────────────

async function handleExportFountain() {
  if (!scriptId.value) return
  fountainExporting.value = true
  try {
    const result = await exportFountain(scriptId.value)
    // Download as file
    const blob = new Blob([result.content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.title}.fountain`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('已导出 Fountain 格式')
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    fountainExporting.value = false
  }
}

function backToProjects() {
  router.push('/projects')
}

// ── Lifecycle ────────────────────────────────────────────────────────────────

onMounted(() => {
  loadScript()
})
</script>

<template>
  <div class="script-editor">
    <!-- Top toolbar -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <el-button :icon="ArrowLeft" text @click="backToProjects">返回项目</el-button>
        <span class="script-title" v-if="script">{{ script.title }}</span>
        <span class="script-title placeholder" v-else>剧本编辑器</span>
      </div>
      <div class="toolbar-right">
        <el-button :icon="MagicStick" @click="openGenerateDialog" type="primary">
          AI 生成剧本
        </el-button>
        <el-button :icon="MagicStick" @click="openRefineDialog" :disabled="!activeScene">
          AI 打磨场景
        </el-button>
        <el-button :icon="View" @click="previewVisible = !previewVisible" :type="previewVisible ? 'primary' : 'default'">
          {{ previewVisible ? '隐藏预览' : '显示预览' }}
        </el-button>
        <el-button :icon="Download" :loading="fountainExporting" @click="handleExportFountain" :disabled="!scriptId">
          导出 Fountain
        </el-button>
      </div>
    </div>

    <!-- Main content -->
    <div class="editor-body">
      <!-- Left: Scene list -->
      <div class="pane scene-list-pane">
        <SceneList
          :scenes="script?.scenes || []"
          :active-scene-id="activeScene?.id ?? null"
          :loading="loading"
          @select="selectScene"
          @add="openAddScene"
          @delete="handleDeleteScene"
        />
      </div>

      <!-- Middle: Scene editor -->
      <div class="pane scene-editor-pane">
        <div v-loading="loading" class="scene-editor-content">
          <!-- Meta info -->
          <div class="meta-section" v-if="script">
            <div class="section-header">
              <span>剧本信息</span>
              <el-button link :icon="Edit" @click="editingMeta = !editingMeta">
                {{ editingMeta ? '取消' : '编辑' }}
              </el-button>
            </div>

            <div v-if="editingMeta" class="meta-edit-form">
              <el-form label-width="80px" size="small">
                <el-form-item label="标题">
                  <el-input v-model="metaForm.title" />
                </el-form-item>
                <el-form-item label="一句话梗概">
                  <el-input v-model="metaForm.logline" type="textarea" :rows="2" />
                </el-form-item>
                <el-form-item label="题材">
                  <el-input v-model="metaForm.genre" style="width: 200px" />
                </el-form-item>
                <el-form-item label="风格">
                  <el-input v-model="metaForm.style" style="width: 200px" />
                </el-form-item>
                <el-form-item label="故事大纲">
                  <el-input v-model="metaForm.synopsis" type="textarea" :rows="4" />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" :icon="Check" @click="saveMeta">保存</el-button>
                </el-form-item>
              </el-form>
            </div>
            <div v-else class="meta-display">
              <p class="meta-logline" v-if="script.logline">{{ script.logline }}</p>
              <div class="meta-tags">
                <el-tag v-if="script.genre" size="small">{{ script.genre }}</el-tag>
                <el-tag v-if="script.style" size="small" type="info">{{ script.style }}</el-tag>
                <el-tag size="small" type="success">{{ script.total_episodes }} 集</el-tag>
              </div>
              <p class="meta-synopsis" v-if="script.synopsis">{{ script.synopsis }}</p>
            </div>
          </div>

          <!-- Scene editor -->
          <div class="scene-section" v-if="activeScene">
            <div class="section-header">
              <span>场景编辑</span>
            </div>

            <!-- Scene basic info -->
            <div class="scene-basic">
              <el-input
                v-model="activeScene.scene_number"
                style="width: 80px"
                size="small"
                @blur="handleUpdateSceneField('scene_number', activeScene.scene_number)"
              />
              <el-select
                v-model="activeScene.int_ext"
                size="small"
                style="width: 90px"
                @change="(val: IntExt) => handleUpdateSceneField('int_ext', val)"
              >
                <el-option label="内景" value="INT" />
                <el-option label="外景" value="EXT" />
                <el-option label="内外景" value="INT/EXT" />
              </el-select>
              <el-input
                v-model="activeScene.location"
                size="small"
                style="flex: 1; min-width: 150px"
                placeholder="场景地点"
                @blur="handleUpdateSceneField('location', activeScene.location)"
              />
              <el-select
                v-model="activeScene.time_of_day"
                size="small"
                style="width: 80px"
                @change="(val: TimeOfDay) => handleUpdateSceneField('time_of_day', val)"
              >
                <el-option label="日" value="日" />
                <el-option label="夜" value="夜" />
                <el-option label="晨" value="晨" />
                <el-option label="昏" value="昏" />
              </el-select>
            </div>

            <!-- Scene description -->
            <div class="scene-desc">
              <div class="sub-label">场景描述 / 动作描写</div>
              <el-input
                v-model="activeScene.description"
                type="textarea"
                :rows="3"
                placeholder="描述这个场景的环境、角色动作和剧情发展..."
                @blur="handleUpdateSceneField('description', activeScene.description)"
              />
            </div>

            <!-- Dialogue editor -->
            <div class="scene-dialogues">
              <DialogueEditor
                :dialogues="activeScene.dialogues || []"
                :loading="dialogueLoading"
                @add="handleAddDialogue"
                @update="handleUpdateDialogue"
                @delete="handleDeleteDialogue"
              />
            </div>
          </div>

          <!-- Empty state -->
          <el-empty
            v-else-if="script"
            description="暂无场景，点击左侧「新增场景」或使用 AI 生成"
            :image-size="80"
          >
            <el-button type="primary" :icon="MagicStick" @click="openGenerateDialog">
              AI 生成剧本
            </el-button>
          </el-empty>

          <el-empty
            v-else
            description="项目暂无剧本，开始创建吧"
            :image-size="80"
          >
            <el-space>
              <el-button type="primary" :icon="MagicStick" @click="openGenerateDialog">
                AI 生成剧本
              </el-button>
            </el-space>
          </el-empty>
        </div>
      </div>

      <!-- Right: Fountain preview -->
      <div class="pane preview-pane" v-if="previewVisible">
        <ScriptPreview :script="script" :loading="loading" />
      </div>
    </div>

    <!-- Generate dialog -->
    <el-dialog v-model="generateDialogVisible" title="AI 生成剧本" width="560px">
      <el-form label-width="100px">
        <el-form-item label="创意描述" required>
          <el-input
            v-model="generateForm.idea"
            type="textarea"
            :rows="4"
            placeholder="描述你的短剧创意，比如：一个重生回到高中的女孩，决定改变命运..."
          />
        </el-form-item>
        <el-form-item label="题材">
          <el-select v-model="generateForm.genre" style="width: 200px">
            <el-option label="都市" value="都市" />
            <el-option label="仙侠" value="仙侠" />
            <el-option label="甜宠" value="甜宠" />
            <el-option label="悬疑" value="悬疑" />
            <el-option label="重生" value="重生" />
            <el-option label="穿越" value="穿越" />
            <el-option label="古装" value="古装" />
            <el-option label="校园" value="校园" />
            <el-option label="职场" value="职场" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="风格">
          <el-input v-model="generateForm.style" placeholder="如：轻松幽默、紧张刺激、温情治愈" />
        </el-form-item>
        <el-form-item label="场景数量">
          <el-input-number v-model="generateForm.num_scenes" :min="3" :max="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="doGenerateScript">
          <el-icon><MagicStick /></el-icon>
          开始生成
        </el-button>
      </template>
    </el-dialog>

    <!-- Refine dialog -->
    <el-dialog v-model="refineDialogVisible" title="AI 打磨场景" width="500px">
      <el-form>
        <el-form-item label="修改意见" required>
          <el-input
            v-model="refineFeedback"
            type="textarea"
            :rows="4"
            placeholder="描述你希望如何修改这个场景，比如：让女主角的情绪更激烈一些，增加一个反转..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="refineDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="refining" @click="doRefineScene">
          <el-icon><MagicStick /></el-icon>
          开始打磨
        </el-button>
      </template>
    </el-dialog>

    <!-- Add scene dialog -->
    <el-dialog v-model="sceneFormVisible" title="新增场景" width="480px">
      <el-form label-width="80px">
        <el-form-item label="场景号">
          <el-input v-model="sceneForm.scene_number" style="width: 120px" />
        </el-form-item>
        <el-form-item label="地点" required>
          <el-input v-model="sceneForm.location" placeholder="例如：主角卧室、咖啡馆、公司会议室" />
        </el-form-item>
        <el-form-item label="内/外景">
          <el-radio-group v-model="sceneForm.int_ext">
            <el-radio value="INT">内景</el-radio>
            <el-radio value="EXT">外景</el-radio>
            <el-radio value="INT/EXT">内外景</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时间">
          <el-radio-group v-model="sceneForm.time_of_day">
            <el-radio value="日">日</el-radio>
            <el-radio value="夜">夜</el-radio>
            <el-radio value="晨">晨</el-radio>
            <el-radio value="昏">昏</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="场景描述">
          <el-input
            v-model="sceneForm.description"
            type="textarea"
            :rows="3"
            placeholder="简要描述这个场景的内容..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sceneFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="sceneLoading" @click="submitScene">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.script-editor {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  background: #fff;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 52px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.script-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.script-title.placeholder {
  color: #909399;
  font-weight: 400;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.pane {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scene-list-pane {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid #ebeef5;
}

.scene-editor-pane {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}

.preview-pane {
  width: 380px;
  flex-shrink: 0;
}

.scene-editor-content {
  padding: 20px 24px;
  height: 100%;
  overflow-y: auto;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.meta-section {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #ebeef5;
}

.meta-logline {
  font-size: 14px;
  color: #606266;
  line-height: 1.7;
  margin: 0 0 10px 0;
  font-style: italic;
}

.meta-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.meta-synopsis {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
  white-space: pre-wrap;
}

.scene-section {
  margin-top: 8px;
}

.scene-basic {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.scene-desc {
  margin-bottom: 16px;
}

.sub-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 6px;
}

.scene-dialogues {
  margin-top: 16px;
  min-height: 200px;
}
</style>
