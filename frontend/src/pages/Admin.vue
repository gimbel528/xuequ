<template>
  <div class="admin-container">
    <div class="admin-header">
      <div class="header-left">
        <h1>学区管理后台</h1>
      </div>
      <div class="header-right">
        <el-button @click="goToMap">
          <el-icon><MapLocation /></el-icon>
          查看地图
        </el-button>
      </div>
    </div>
    
    <div class="admin-content">
      <div class="school-panel">
        <div class="panel-header">
          <span>学校列表</span>
          <el-button type="primary" size="small" @click="openAddDialog">
            <el-icon><Plus /></el-icon>
            添加学校
          </el-button>
        </div>
        <div class="panel-content">
          <el-table :data="schools" v-loading="loading" stripe>
            <el-table-column prop="name" label="学校名称" min-width="150" />
            <el-table-column prop="address" label="地址" min-width="200" show-overflow-tooltip />
            <el-table-column prop="phone" label="电话" width="130" />
            <el-table-column label="小区数量" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="info" size="small">
                  {{ row.communities?.length || 0 }} 个
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="颜色" width="80" align="center">
              <template #default="{ row }">
                <div class="color-preview" :style="{ backgroundColor: row.color }"></div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="320" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-button type="success" link size="small" @click="openCommunityDialog(row)">
                  小区管理
                </el-button>
                <el-button type="warning" link size="small" @click="openPositionDialog(row)">
                  调整位置
                </el-button>
                <el-button type="danger" link size="small" @click="deleteSchool(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>

    <el-dialog 
      v-model="schoolDialogVisible" 
      :title="isEdit ? '编辑学校' : '添加学校'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="schoolForm" label-width="80px">
        <el-form-item label="学校名称" required>
          <el-input v-model="schoolForm.name" placeholder="请输入学校名称" />
        </el-form-item>
        <el-form-item label="学校地址">
          <el-input v-model="schoolForm.address" placeholder="请输入学校地址" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="schoolForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="学校简介">
          <el-input 
            v-model="schoolForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入学校简介"
          />
        </el-form-item>
        <el-form-item label="学区颜色">
          <el-color-picker v-model="schoolForm.color" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="schoolDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveSchool" :loading="saving">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog 
      v-model="communityDialogVisible" 
      :title="`小区管理 - ${currentSchool?.name}`"
      width="90%"
      top="5vh"
      destroy-on-close
    >
      <div class="community-container">
        <div class="community-list">
          <div class="community-list-header">
            <span>小区列表</span>
            <el-button type="primary" size="small" @click="openAddCommunityDialog">
              添加小区
            </el-button>
          </div>
          <div class="community-list-content">
            <div 
              v-for="community in currentSchool?.communities || []" 
              :key="community.id"
              class="community-item"
            >
              <div class="community-name">{{ community.name }}</div>
              <div class="community-actions">
                <el-button type="primary" link size="small" @click="openDrawCommunityDialog(community)">
                  绘制边界
                </el-button>
                <el-button type="danger" link size="small" @click="deleteCommunity(community)">
                  删除
                </el-button>
              </div>
            </div>
            <div v-if="!currentSchool?.communities?.length" class="empty-tip">
              暂无小区，请添加
            </div>
          </div>
        </div>
        <div class="community-map" id="communityMap"></div>
      </div>
    </el-dialog>

    <el-dialog 
      v-model="addCommunityDialogVisible" 
      title="添加小区"
      width="400px"
      destroy-on-close
    >
      <el-form :model="communityForm" label-width="80px">
        <el-form-item label="小区名称" required>
          <el-input v-model="communityForm.name" placeholder="请输入小区名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addCommunityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addCommunity" :loading="saving">添加</el-button>
      </template>
    </el-dialog>

    <el-dialog 
      v-model="drawCommunityDialogVisible" 
      :title="`绘制边界 - ${currentCommunity?.name}`"
      width="90%"
      top="5vh"
      destroy-on-close
    >
      <div class="draw-container">
        <div class="draw-map" id="drawCommunityMap"></div>
        <div class="draw-sidebar">
          <div class="draw-tips">
            <h3>绘制说明</h3>
            <ol>
              <li>在地图上点击开始绘制</li>
              <li>依次点击添加顶点</li>
              <li>至少需要3个顶点</li>
              <li>可随时清除重新绘制</li>
            </ol>
          </div>
          <div class="draw-info" v-if="communityPolygonPoints.length > 0">
            <span>已绘制 {{ communityPolygonPoints.length }} 个顶点</span>
          </div>
          <div class="draw-actions">
            <el-button @click="clearCommunityPolygon">清除绘制</el-button>
            <el-button type="primary" @click="saveCommunityPolygon" :loading="saving">
              保存边界
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog 
      v-model="positionDialogVisible" 
      :title="`调整学校位置 - ${currentSchool?.name}`"
      width="90%"
      top="5vh"
      destroy-on-close
    >
      <div class="position-container">
        <div class="position-map" id="positionMap"></div>
        <div class="position-sidebar">
          <div class="position-tips">
            <h3>操作说明</h3>
            <ol>
              <li>地图上的标记为当前学校位置</li>
              <li>拖拽标记到正确位置</li>
              <li>点击保存完成调整</li>
            </ol>
          </div>
          <div class="position-info" v-if="currentPosition">
            <p><strong>经度:</strong> {{ currentPosition[0].toFixed(6) }}</p>
            <p><strong>纬度:</strong> {{ currentPosition[1].toFixed(6) }}</p>
          </div>
          <div class="position-actions">
            <el-button @click="positionDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="savePosition" :loading="saving">
              保存位置
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { schoolApi, communityApi } from '@/api'
import type { School, SchoolForm, Community, CommunityForm } from '@/types'

declare const AMap: any

const router = useRouter()
const schools = ref<School[]>([])
const loading = ref(true)
const saving = ref(false)
const schoolDialogVisible = ref(false)
const communityDialogVisible = ref(false)
const addCommunityDialogVisible = ref(false)
const drawCommunityDialogVisible = ref(false)
const positionDialogVisible = ref(false)
const isEdit = ref(false)
const currentSchool = ref<School | null>(null)
const currentCommunity = ref<Community | null>(null)
const schoolForm = ref<SchoolForm>({
  name: '',
  address: '',
  phone: '',
  description: '',
  color: '#3388ff'
})
const communityForm = ref<CommunityForm>({
  name: '',
  coordinates: ''
})
const currentPosition = ref<[number, number] | null>(null)

let communityMap: any = null
let positionMap: any = null
let positionMarker: any = null
let drawCommunityMap: any = null
let communityPolygon: any = null
let communityPolygonPoints: any[] = []
let communityPolygons: any[] = []

const AMAP_KEY = '11280b7f874f195dd2edf188a10f8429'

const loadSchools = async () => {
  loading.value = true
  try {
    const { data } = await schoolApi.getAll()
    schools.value = data
  } catch (error) {
    ElMessage.error('加载学校数据失败')
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  isEdit.value = false
  currentSchool.value = null
  schoolForm.value = {
    name: '',
    address: '',
    phone: '',
    description: '',
    color: '#3388ff'
  }
  schoolDialogVisible.value = true
}

const openEditDialog = (school: School) => {
  isEdit.value = true
  currentSchool.value = school
  schoolForm.value = {
    name: school.name,
    address: school.address || '',
    phone: school.phone || '',
    description: school.description || '',
    color: school.color
  }
  schoolDialogVisible.value = true
}

const saveSchool = async () => {
  if (!schoolForm.value.name.trim()) {
    ElMessage.warning('请输入学校名称')
    return
  }

  saving.value = true
  try {
    if (isEdit.value && currentSchool.value) {
      await schoolApi.update(currentSchool.value.id, schoolForm.value)
      ElMessage.success('更新成功')
    } else {
      await schoolApi.create(schoolForm.value)
      ElMessage.success('添加成功')
    }
    schoolDialogVisible.value = false
    await loadSchools()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const deleteSchool = async (school: School) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除"${school.name}"吗？删除后无法恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    
    await schoolApi.delete(school.id)
    ElMessage.success('删除成功')
    await loadSchools()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const openCommunityDialog = async (school: School) => {
  currentSchool.value = school
  communityDialogVisible.value = true
  
  await nextTick()
  initCommunityMap()
}

const initCommunityMap = () => {
  if (communityMap) {
    communityMap.destroy()
  }

  communityMap = new AMap.Map('communityMap', {
    zoom: 12,
    center: [121.78, 39.05]
  })

  communityPolygons.forEach(p => communityMap.remove(p))
  communityPolygons = []

  if (currentSchool.value?.longitude && currentSchool.value?.latitude) {
    communityMap.setCenter([currentSchool.value.longitude, currentSchool.value.latitude])
    
    const marker = new AMap.Marker({
      position: [currentSchool.value.longitude, currentSchool.value.latitude],
      anchor: 'bottom-center'
    })
    communityMap.add(marker)
  }

  if (currentSchool.value?.communities) {
    currentSchool.value.communities.forEach(c => {
      try {
        const coords = JSON.parse(c.coordinates)
        const path = coords.map((p: number[]) => new AMap.LngLat(p[0], p[1]))
        
        const polygon = new AMap.Polygon({
          path: path,
          strokeColor: currentSchool.value?.color || '#3388ff',
          strokeWeight: 2,
          fillColor: currentSchool.value?.color || '#3388ff',
          fillOpacity: 0.3
        })
        communityMap.add(polygon)
        communityPolygons.push(polygon)
      } catch (e) {
        console.error('解析小区边界失败:', c.name)
      }
    })
  }
}

const openAddCommunityDialog = () => {
  communityForm.value = {
    name: '',
    coordinates: ''
  }
  addCommunityDialogVisible.value = true
}

const addCommunity = async () => {
  if (!communityForm.value.name.trim()) {
    ElMessage.warning('请输入小区名称')
    return
  }

  saving.value = true
  try {
    await communityApi.create(currentSchool.value!.id, {
      name: communityForm.value.name,
      coordinates: '[]'
    })
    ElMessage.success('添加成功')
    addCommunityDialogVisible.value = false
    await loadSchools()
    currentSchool.value = schools.value.find(s => s.id === currentSchool.value?.id) || null
    initCommunityMap()
  } catch (error) {
    ElMessage.error('添加失败')
  } finally {
    saving.value = false
  }
}

const openDrawCommunityDialog = async (community: Community) => {
  currentCommunity.value = community
  drawCommunityDialogVisible.value = true
  
  await nextTick()
  initDrawCommunityMap()
}

const initDrawCommunityMap = () => {
  if (drawCommunityMap) {
    drawCommunityMap.destroy()
  }

  let center = [121.78, 39.05]
  if (currentSchool.value?.longitude && currentSchool.value?.latitude) {
    center = [currentSchool.value.longitude, currentSchool.value.latitude]
  }

  drawCommunityMap = new AMap.Map('drawCommunityMap', {
    zoom: 14,
    center: center
  })

  communityPolygonPoints = []
  communityPolygon = null

  if (currentCommunity.value?.coordinates) {
    try {
      const coords = JSON.parse(currentCommunity.value.coordinates)
      if (coords.length >= 3) {
        const path = coords.map((c: number[]) => new AMap.LngLat(c[0], c[1]))
        communityPolygon = new AMap.Polygon({
          path: path,
          strokeColor: currentSchool.value?.color || '#3388ff',
          strokeWeight: 2,
          fillColor: currentSchool.value?.color || '#3388ff',
          fillOpacity: 0.3
        })
        drawCommunityMap.add(communityPolygon)
        communityPolygonPoints = coords
        drawCommunityMap.setFitView([communityPolygon])
      }
    } catch (e) {
      console.error('解析已有边界失败:', e)
    }
  }

  drawCommunityMap.on('click', handleCommunityMapClick)
}

const handleCommunityMapClick = (e: any) => {
  const lngLat = [e.lnglat.getLng(), e.lnglat.getLat()]
  communityPolygonPoints.push(lngLat)
  
  if (communityPolygon) {
    drawCommunityMap.remove(communityPolygon)
  }
  
  if (communityPolygonPoints.length >= 3) {
    const path = communityPolygonPoints.map(p => new AMap.LngLat(p[0], p[1]))
    communityPolygon = new AMap.Polygon({
      path: path,
      strokeColor: currentSchool.value?.color || '#3388ff',
      strokeWeight: 2,
      fillColor: currentSchool.value?.color || '#3388ff',
      fillOpacity: 0.3
    })
    drawCommunityMap.add(communityPolygon)
  }
  
  drawCommunityMap.setDefaultCursor('crosshair')
}

const clearCommunityPolygon = () => {
  if (communityPolygon) {
    drawCommunityMap.remove(communityPolygon)
    communityPolygon = null
  }
  communityPolygonPoints = []
}

const saveCommunityPolygon = async () => {
  if (communityPolygonPoints.length < 3) {
    ElMessage.warning('请至少绘制3个顶点')
    return
  }

  saving.value = true
  try {
    const coordinates = JSON.stringify(communityPolygonPoints)
    
    await communityApi.update(currentCommunity.value!.id, {
      coordinates: coordinates
    })
    
    ElMessage.success('保存成功')
    drawCommunityDialogVisible.value = false
    await loadSchools()
    currentSchool.value = schools.value.find(s => s.id === currentSchool.value?.id) || null
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const deleteCommunity = async (community: Community) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除小区"${community.name}"吗？`,
      '删除确认',
      { type: 'warning' }
    )
    
    await communityApi.delete(community.id)
    ElMessage.success('删除成功')
    await loadSchools()
    currentSchool.value = schools.value.find(s => s.id === currentSchool.value?.id) || null
    initCommunityMap()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const openPositionDialog = async (school: School) => {
  currentSchool.value = school
  positionDialogVisible.value = true
  
  await nextTick()
  initPositionMap()
}

const initPositionMap = () => {
  if (positionMap) {
    positionMap.destroy()
  }

  let center = [121.78, 39.05]
  if (currentSchool.value?.longitude && currentSchool.value?.latitude) {
    center = [currentSchool.value.longitude, currentSchool.value.latitude]
    currentPosition.value = [currentSchool.value.longitude, currentSchool.value.latitude]
  }

  positionMap = new AMap.Map('positionMap', {
    zoom: 16,
    center: center
  })

  positionMarker = new AMap.Marker({
    position: center,
    draggable: true,
    cursor: 'move',
    anchor: 'bottom-center'
  })
  positionMap.add(positionMarker)

  positionMarker.on('dragging', (e: any) => {
    currentPosition.value = [e.lnglat.getLng(), e.lnglat.getLat()]
  })

  positionMarker.on('dragend', (e: any) => {
    currentPosition.value = [e.lnglat.getLng(), e.lnglat.getLat()]
  })

  if (currentSchool.value?.communities) {
    currentSchool.value.communities.forEach(c => {
      try {
        const coords = JSON.parse(c.coordinates)
        if (coords.length >= 3) {
          const path = coords.map((p: number[]) => new AMap.LngLat(p[0], p[1]))
          const polygon = new AMap.Polygon({
            path: path,
            strokeColor: currentSchool.value?.color || '#3388ff',
            strokeWeight: 2,
            fillColor: currentSchool.value?.color || '#3388ff',
            fillOpacity: 0.15
          })
          positionMap.add(polygon)
        }
      } catch (e) {
        console.error('解析小区边界失败')
      }
    })
  }
}

const savePosition = async () => {
  if (!currentPosition.value) {
    ElMessage.warning('请先确定学校位置')
    return
  }

  saving.value = true
  try {
    await schoolApi.update(currentSchool.value!.id, {
      longitude: currentPosition.value[0],
      latitude: currentPosition.value[1]
    })
    
    ElMessage.success('位置已更新')
    positionDialogVisible.value = false
    await loadSchools()
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const goToMap = () => {
  router.push('/')
}

const loadAMapScript = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if ((window as any).AMap) {
      resolve()
      return
    }
    
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('高德地图加载失败'))
    document.head.appendChild(script)
  })
}

onMounted(async () => {
  try {
    await loadAMapScript()
    await loadSchools()
  } catch (error) {
    ElMessage.error('初始化失败')
  }
})
</script>

<style scoped>
.admin-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.admin-header {
  height: 60px;
  background: white;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.admin-header h1 {
  font-size: 20px;
  color: #303133;
}

.admin-content {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.school-panel {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.panel-header {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header span {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.panel-content {
  padding: 20px;
}

.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: inline-block;
}

.community-container {
  display: flex;
  height: 70vh;
}

.community-list {
  width: 300px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.community-list-header {
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #303133;
}

.community-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.community-item {
  background: white;
  padding: 12px 15px;
  border-radius: 6px;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.community-name {
  font-size: 14px;
  color: #303133;
}

.community-actions {
  display: flex;
  gap: 5px;
}

.empty-tip {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.community-map {
  flex: 1;
}

.draw-container {
  display: flex;
  height: 70vh;
}

.draw-map {
  flex: 1;
}

.draw-sidebar {
  width: 250px;
  padding: 20px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.draw-tips h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.draw-tips ol {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 2;
}

.draw-info {
  margin-top: 20px;
  padding: 10px;
  background: white;
  border-radius: 4px;
  text-align: center;
  color: #409eff;
}

.draw-actions {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.position-container {
  display: flex;
  height: 70vh;
}

.position-map {
  flex: 1;
}

.position-sidebar {
  width: 250px;
  padding: 20px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.position-tips h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #303133;
}

.position-tips ol {
  margin: 0;
  padding-left: 20px;
  color: #606266;
  line-height: 2;
}

.position-info {
  margin-top: 20px;
  padding: 15px;
  background: white;
  border-radius: 4px;
}

.position-info p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
}

.position-info p:last-child {
  margin-bottom: 0;
}

.position-actions {
  margin-top: auto;
  display: flex;
  gap: 10px;
}
</style>
