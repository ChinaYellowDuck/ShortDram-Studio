<script setup lang="ts">
import {
  ArrowDown,
  ArrowUp,
  Delete,
  Edit,
  Film,
  MagicStick,
  PictureFilled,
  Plus,
  Search,
  Sort,
  VideoCamera,
} from '@element-plus/icons-vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
} from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ScriptWizardView from './ScriptWizardView.vue'

import { errorMessage } from '../api/client'
import {
  createAsset,
  deleteAsset,
  listAssets,
  updateAsset,
} from '../api/assets'
import { transitionProjectPhase } from '../api/projects'
import {
  createStoryboardShot,
  deleteStoryboardShot,
  listStoryboardShots,
  reorderStoryboard,
  updateStoryboardShot,
} from '../api/storyboard'
import type {
  Asset,
  AssetCreate,
  AssetType,
  ProjectPhase,
  StoryboardShot,
  StoryboardShotCreate,
  StoryboardShotUpdate,
} from '../api/types'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => Number(route.params.projectId))

// ── 阶段配置 ───────────────────────────────────────────────
const phaseSteps: { key: ProjectPhase; label: string; icon: any; desc: string }[] = [
  { key: 'script', label: '剧本创作', icon: MagicStick, desc: '导入小说、生成大纲与剧本' },
  { key: 'asset', label: '资产管理', icon: PictureFilled, desc: '人物/场景/道具统一资产库' },
  { key: 'storyboard', label: '分镜制作', icon: Film, desc: '场景级分镜设计' },
  { key: 'video', label: '视频合成', icon: VideoCamera, desc: '片段生成、配音、合成' },
  { key: 'completed', label: '项目完成', icon: VideoCamera, desc: '成片交付' },
]

// ── 状态 ───────────────────────────────────────────────────
const activeModule = ref<'script' | 'asset' | 'storyboard' | 'video'>('script')
const projectPhase = ref<ProjectPhase>('script')
const projectName = ref('')
const transitioning = ref(false)

const currentPhaseIndex = computed(() =>
  phaseSteps.findIndex((s) => s.key === projectPhase.value),
)

// ── 阶段切换 ───────────────────────────────────────────────
async function goToPhase(target: ProjectPhase) {
  const currentIdx = currentPhaseIndex.value
  const targetIdx = phaseSteps.findIndex((s) => s.key === target)
  const direction = targetIdx > currentIdx ? '推进' : '回退'
  const targetLabel = phaseSteps[targetIdx].label

  try {
    await ElMessageBox.confirm(
      `确定${direction}到「${targetLabel}」阶段吗？`,
      `${direction}阶段`,
      { type: direction === '推进' ? 'primary' : 'warning' },
    )
  } catch {
    return
  }

  transitioning.value = true
  try {
    const updated = await transitionProjectPhase(projectId.value, target)
    projectPhase.value = updated.phase
    projectName.value = updated.name
    ElMessage.success(`已${direction}到「${targetLabel}」阶段`)
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    transitioning.value = false
  }
}

// ── 资产模块 ───────────────────────────────────────────────
const assetLoading = ref(false)
const assets = ref<Asset[]>([])
const assetTotal = ref(0)
const assetPage = ref(1)
const assetPageSize = ref(20)
const assetType = ref<AssetType | ''>('')
const assetSearch = ref('')

const assetDialogVisible = ref(false)
const assetEditing = ref<Asset | null>(null)
const assetSubmitting = ref(false)
const assetFormRef = ref<FormInstance>()
const assetForm = reactive<AssetCreate>({
  type: 'character',
  name: '',
  description: '',
  extra: {},
})

const assetRules: FormRules = {
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择资产类型', trigger: 'change' }],
}

const assetTypeOptions: { value: AssetType; label: string }[] = [
  { value: 'character', label: '人物' },
  { value: 'scene', label: '场景' },
  { value: 'prop', label: '道具' },
]

const assetTypeMeta: Record<AssetType, { label: string; color: string }> = {
  character: { label: '人物', color: '#67c23a' },
  scene: { label: '场景', color: '#409eff' },
  prop: { label: '道具', color: '#e6a23c' },
}

async function loadAssets() {
  assetLoading.value = true
  try {
    const res = await listAssets({
      project_id: projectId.value,
      page: assetPage.value,
      page_size: assetPageSize.value,
      type: assetType.value || undefined,
      search: assetSearch.value || undefined,
    })
    assets.value = res.items
    assetTotal.value = res.total
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    assetLoading.value = false
  }
}

function openCreateAsset() {
  assetEditing.value = null
  assetForm.type = 'character'
  assetForm.name = ''
  assetForm.description = ''
  assetForm.extra = {}
  assetDialogVisible.value = true
}

function openEditAsset(asset: Asset) {
  assetEditing.value = asset
  assetForm.type = asset.type
  assetForm.name = asset.name
  assetForm.description = asset.description || ''
  assetForm.extra = asset.extra || {}
  assetDialogVisible.value = true
}

async function submitAsset() {
  const valid = await assetFormRef.value?.validate().catch(() => false)
  if (!valid) return
  assetSubmitting.value = true
  try {
    if (assetEditing.value) {
      await updateAsset(assetEditing.value.id, assetForm)
      ElMessage.success('资产已更新')
    } else {
      await createAsset(projectId.value, assetForm)
      ElMessage.success('资产创建成功')
    }
    assetDialogVisible.value = false
    await loadAssets()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    assetSubmitting.value = false
  }
}

async function removeAsset(asset: Asset) {
  try {
    await ElMessageBox.confirm(`确定删除资产「${asset.name}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteAsset(asset.id)
    ElMessage.success('已删除')
    await loadAssets()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

// ── 分镜模块 ───────────────────────────────────────────────
const shotLoading = ref(false)
const shots = ref<StoryboardShot[]>([])
const shotTotal = ref(0)
const shotPage = ref(1)
const shotPageSize = ref(50)

const shotDialogVisible = ref(false)
const shotEditing = ref<StoryboardShot | null>(null)
const shotSubmitting = ref(false)
const shotFormRef = ref<FormInstance>()
const shotForm = reactive<StoryboardShotCreate>({
  script_scene_id: 0,
  shot_number: '',
  composition: '中景',
  camera_movement: '固定',
  camera_angle: '平视',
  visual_description: '',
  duration_seconds: 5,
  character_ids: [],
  prop_ids: [],
})

const shotRules: FormRules = {
  shot_number: [{ required: true, message: '请输入镜头编号', trigger: 'blur' }],
  script_scene_id: [{ required: true, message: '请输入关联场景ID', trigger: 'blur' }],
}

const compositionOptions = ['大远景', '远景', '全景', '中景', '中近景', '近景', '特写']
const movementOptions = ['固定', '推', '拉', '摇', '移', '跟', '变焦']
const angleOptions = ['平视', '仰视', '俯视', '侧视', '倾斜']

async function loadShots() {
  shotLoading.value = true
  try {
    const res = await listStoryboardShots({
      project_id: projectId.value,
      page: shotPage.value,
      page_size: shotPageSize.value,
    })
    shots.value = res.items
    shotTotal.value = res.total
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    shotLoading.value = false
  }
}

function openCreateShot() {
  shotEditing.value = null
  shotForm.script_scene_id = 0
  shotForm.shot_number = ''
  shotForm.composition = '中景'
  shotForm.camera_movement = '固定'
  shotForm.camera_angle = '平视'
  shotForm.visual_description = ''
  shotForm.duration_seconds = 5
  shotForm.character_ids = []
  shotForm.prop_ids = []
  shotDialogVisible.value = true
}

function openEditShot(shot: StoryboardShot) {
  shotEditing.value = shot
  shotForm.script_scene_id = shot.script_scene_id
  shotForm.shot_number = shot.shot_number
  shotForm.composition = shot.composition
  shotForm.camera_movement = shot.camera_movement
  shotForm.camera_angle = shot.camera_angle
  shotForm.visual_description = shot.visual_description || ''
  shotForm.duration_seconds = shot.duration_seconds
  shotForm.character_ids = shot.character_ids || []
  shotForm.prop_ids = shot.prop_ids || []
  shotDialogVisible.value = true
}

async function submitShot() {
  const valid = await shotFormRef.value?.validate().catch(() => false)
  if (!valid) return
  shotSubmitting.value = true
  try {
    if (shotEditing.value) {
      await updateStoryboardShot(shotEditing.value.id, shotForm as StoryboardShotUpdate)
      ElMessage.success('分镜已更新')
    } else {
      await createStoryboardShot(projectId.value, shotForm)
      ElMessage.success('分镜创建成功')
    }
    shotDialogVisible.value = false
    await loadShots()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  } finally {
    shotSubmitting.value = false
  }
}

async function removeShot(shot: StoryboardShot) {
  try {
    await ElMessageBox.confirm(`确定删除分镜「${shot.shot_number}」吗？`, '删除确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteStoryboardShot(shot.id)
    ElMessage.success('已删除')
    await loadShots()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

async function moveShot(index: number, direction: -1 | 1) {
  const newIndex = index + direction
  if (newIndex < 0 || newIndex >= shots.value.length) return
  const newShots = [...shots.value]
  ;[newShots[index], newShots[newIndex]] = [newShots[newIndex], newShots[index]]
  try {
    await reorderStoryboard(projectId.value, newShots.map((s) => s.id))
    ElMessage.success('顺序已更新')
    await loadShots()
  } catch (err) {
    ElMessage.error(errorMessage(err))
  }
}

// ── 生命周期 ───────────────────────────────────────────────
onMounted(async () => {
  // 从 URL 读取默认 tab
  const tab = route.query.tab as string | undefined
  if (tab && ['script', 'asset', 'storyboard', 'video'].includes(tab)) {
    activeModule.value = tab as typeof activeModule.value
  }

  // 加载资产（如果是资产 tab）
  if (activeModule.value === 'asset') {
    loadAssets()
  }
  if (activeModule.value === 'storyboard') {
    loadShots()
  }
})

function handleTabChange(tabName: string) {
  if (tabName === 'asset' && assets.value.length === 0) {
    loadAssets()
  }
  if (tabName === 'storyboard' && shots.value.length === 0) {
    loadShots()
  }
}
</script>

<template>
  <div class="workspace-page">
    <!-- 顶部：项目名 + 阶段进度条 -->
    <div class="workspace-header">
      <div class="project-info">
        <h2>{{ projectName || '项目工作台' }}</h2>
        <p class="project-desc">短剧制作流水线：剧本 → 资产 → 分镜 → 视频</p>
      </div>
      <el-button @click="router.push('/projects')">返回项目列表</el-button>
    </div>

    <!-- 五阶段进度条 -->
    <el-card shadow="never" class="phase-card">
      <el-steps :active="currentPhaseIndex + 1" finish-status="success" align-center>
        <el-step v-for="step in phaseSteps" :key="step.key" :title="step.label" :description="step.desc">
          <template #icon>
            <el-icon :size="20"><component :is="step.icon" /></el-icon>
          </template>
        </el-step>
      </el-steps>

      <div class="phase-actions">
        <el-button
          v-if="currentPhaseIndex > 0"
          :icon="ArrowUp"
          :loading="transitioning"
          @click="goToPhase(phaseSteps[currentPhaseIndex - 1].key)"
        >
          回退到上一阶段
        </el-button>
        <el-button
          v-if="currentPhaseIndex < phaseSteps.length - 1"
          type="primary"
          :icon="ArrowDown"
          :loading="transitioning"
          @click="goToPhase(phaseSteps[currentPhaseIndex + 1].key)"
        >
          推进到下一阶段
        </el-button>
      </div>
    </el-card>

    <!-- 四大模块 Tab -->
    <el-card shadow="never" class="modules-card">
      <el-tabs v-model="activeModule" class="modules-tabs" @tab-change="handleTabChange">
        <!-- 剧本模块 -->
        <el-tab-pane label="剧本管理" name="script">
          <ScriptWizardView />
        </el-tab-pane>

        <!-- 资产模块 -->
        <el-tab-pane label="资产管理" name="asset">
          <div class="asset-toolbar">
            <el-space>
              <el-radio-group v-model="assetType" @change="assetPage = 1; loadAssets()">
                <el-radio-button value="">全部</el-radio-button>
                <el-radio-button value="character">人物</el-radio-button>
                <el-radio-button value="scene">场景</el-radio-button>
                <el-radio-button value="prop">道具</el-radio-button>
              </el-radio-group>
              <el-input
                v-model="assetSearch"
                placeholder="按名称搜索"
                clearable
                style="width: 200px"
                @keyup.enter="assetPage = 1; loadAssets()"
                @clear="loadAssets()"
              >
                <template #prefix><el-icon><Search /></el-icon></template>
              </el-input>
            </el-space>
            <el-button type="primary" :icon="Plus" @click="openCreateAsset">
              新建资产
            </el-button>
          </div>

          <div v-loading="assetLoading" class="asset-grid">
            <div v-for="asset in assets" :key="asset.id" class="asset-card">
              <div class="asset-card-header">
                <el-tag
                  size="small"
                  :style="{ background: assetTypeMeta[asset.type].color + '20', color: assetTypeMeta[asset.type].color, borderColor: assetTypeMeta[asset.type].color + '40' }"
                >
                  {{ assetTypeMeta[asset.type].label }}
                </el-tag>
                <span class="ref-count">引用 {{ asset.reference_count }}</span>
              </div>
              <div class="asset-card-body">
                <h4 class="asset-name">{{ asset.name }}</h4>
                <p class="asset-desc">{{ asset.description || '暂无描述' }}</p>
                <div v-if="asset.extra && Object.keys(asset.extra).length" class="asset-extra">
                  <el-tag
                    v-for="(v, k) in asset.extra"
                    :key="String(k)"
                    size="small"
                    type="info"
                    effect="plain"
                  >
                    {{ k }}: {{ v }}
                  </el-tag>
                </div>
              </div>
              <div class="asset-card-footer">
                <el-button type="primary" link :icon="Edit" @click="openEditAsset(asset)">编辑</el-button>
                <el-button type="danger" link :icon="Delete" @click="removeAsset(asset)">删除</el-button>
              </div>
            </div>

            <div v-if="!assetLoading && assets.length === 0" class="empty-tip">
              暂无资产，点击右上角「新建资产」添加
            </div>
          </div>

          <el-pagination
            v-if="assetTotal > assetPageSize"
            style="margin-top: 16px; justify-content: flex-end"
            layout="total, prev, pager, next"
            :total="assetTotal"
            :page-size="assetPageSize"
            v-model:current-page="assetPage"
            @current-change="loadAssets()"
          />
        </el-tab-pane>

        <!-- 分镜模块 -->
        <el-tab-pane label="分镜管理" name="storyboard">
          <div class="shot-toolbar">
            <div class="shot-info">
              <el-tag type="info" effect="plain">共 {{ shotTotal }} 个分镜</el-tag>
            </div>
            <el-button type="primary" :icon="Plus" @click="openCreateShot">
              新建分镜
            </el-button>
          </div>

          <el-table :data="shots" v-loading="shotLoading" empty-text="暂无分镜">
            <el-table-column label="序号" width="70" type="index" />
            <el-table-column prop="shot_number" label="镜头编号" width="120" />
            <el-table-column prop="composition" label="景别" width="90" />
            <el-table-column prop="camera_movement" label="运镜" width="90" />
            <el-table-column prop="camera_angle" label="角度" width="90" />
            <el-table-column prop="duration_seconds" label="时长(秒)" width="100" />
            <el-table-column prop="visual_description" label="画面描述" min-width="200" show-overflow-tooltip>
              <template #default="{ row }">{{ row.visual_description || '-' }}</template>
            </el-table-column>
            <el-table-column label="操作" width="180">
              <template #default="{ row, $index }">
                <el-button link :icon="Sort" size="small" :disabled="$index === 0" @click="moveShot($index, -1)">上移</el-button>
                <el-button link :icon="Sort" size="small" :disabled="$index === shots.length - 1" @click="moveShot($index, 1)">下移</el-button>
                <el-button type="primary" link :icon="Edit" @click="openEditShot(row)">编辑</el-button>
                <el-button type="danger" link :icon="Delete" @click="removeShot(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="shotTotal > shotPageSize"
            style="margin-top: 16px; justify-content: flex-end"
            layout="total, prev, pager, next"
            :total="shotTotal"
            :page-size="shotPageSize"
            v-model:current-page="shotPage"
            @current-change="loadShots()"
          />
        </el-tab-pane>

        <!-- 视频模块 -->
        <el-tab-pane label="视频合成" name="video">
          <div class="module-placeholder">
            <el-icon :size="64" color="#e6a23c"><VideoCamera /></el-icon>
            <h3>视频合成工作台</h3>
            <p>半自动化分步模式：片段生成 → 配音 → 最终合成，每步可预览调整</p>
            <el-alert title="即将上线" type="info" :closable="false" style="max-width: 400px" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- 资产编辑弹窗 -->
    <el-dialog v-model="assetDialogVisible" :title="assetEditing ? '编辑资产' : '新建资产'" width="480px">
      <el-form ref="assetFormRef" :model="assetForm" :rules="assetRules" label-width="80px">
        <el-form-item label="资产类型" prop="type">
          <el-select v-model="assetForm.type" style="width: 100%">
            <el-option v-for="opt in assetTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="assetForm.name" maxlength="200" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="assetForm.description" type="textarea" :rows="3" placeholder="AI 生成时使用的详细描述" />
        </el-form-item>
        <el-form-item label="图片URL">
          <el-input v-model="assetForm.image_url" placeholder="参考图 URL 或路径" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assetDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="assetSubmitting" @click="submitAsset">
          {{ assetEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 分镜编辑弹窗 -->
    <el-dialog v-model="shotDialogVisible" :title="shotEditing ? '编辑分镜' : '新建分镜'" width="560px">
      <el-form ref="shotFormRef" :model="shotForm" :rules="shotRules" label-width="100px">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="镜头编号" prop="shot_number">
              <el-input v-model="shotForm.shot_number" placeholder="例如 S01E01-001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="场景ID" prop="script_scene_id">
              <el-input-number v-model="shotForm.script_scene_id" :min="1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="景别">
              <el-select v-model="shotForm.composition" style="width: 100%">
                <el-option v-for="opt in compositionOptions" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="运镜">
              <el-select v-model="shotForm.camera_movement" style="width: 100%">
                <el-option v-for="opt in movementOptions" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="角度">
              <el-select v-model="shotForm.camera_angle" style="width: 100%">
                <el-option v-for="opt in angleOptions" :key="opt" :label="opt" :value="opt" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="时长(秒)">
              <el-input-number v-model="shotForm.duration_seconds" :min="1" :max="300" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关键帧">
              <el-input v-model="shotForm.key_frame_url" placeholder="关键帧图片 URL" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="画面描述">
          <el-input
            v-model="shotForm.visual_description"
            type="textarea"
            :rows="3"
            placeholder="详细的画面描述，用于视频生成"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="shotDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="shotSubmitting" @click="submitShot">
          {{ shotEditing ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.workspace-page {
  padding: 24px;
  min-height: 100vh;
  background: var(--el-bg-color-page);
}

.workspace-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.workspace-header h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.project-desc {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.phase-card {
  margin-bottom: 16px;
}

.phase-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
}

.modules-card {
  min-height: 500px;
}

.modules-tabs {
  padding: 0 8px;
}

.module-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.module-placeholder h3 {
  margin: 16px 0 8px 0;
  font-size: 20px;
  color: var(--el-text-color-primary);
}

.module-placeholder p {
  margin: 0 0 20px 0;
  font-size: 14px;
  max-width: 400px;
}

/* 资产模块 */
.asset-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.asset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  min-height: 200px;
}

.asset-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-bg-color);
  display: flex;
  flex-direction: column;
  transition: all 0.2s;
}

.asset-card:hover {
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.asset-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.ref-count {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.asset-card-body {
  padding: 12px;
  flex: 1;
}

.asset-name {
  margin: 0 0 6px 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.asset-desc {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.asset-extra {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.asset-card-footer {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  padding: 8px 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.empty-tip {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: var(--el-text-color-placeholder);
}

/* 分镜模块 */
.shot-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
