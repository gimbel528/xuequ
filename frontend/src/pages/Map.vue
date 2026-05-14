<template>
  <div class="map-container">
    <div id="map" ref="mapContainer"></div>
    <div class="map-header">
      <h1>大连金普新区学区地图</h1>
      <el-button type="primary" @click="goToAdmin">
        <el-icon><Setting /></el-icon>
        后台管理
      </el-button>
    </div>
    <div class="school-list-toggle" v-if="schools.length > 0" @click="listVisible = !listVisible">
      <el-icon class="toggle-arrow" :class="{ expanded: listVisible }"><ArrowRight /></el-icon>
      <span>学校列表 ({{ schools.length }})</span>
    </div>
    <div class="school-list" v-if="schools.length > 0 && listVisible">
      <div class="school-list-content">
        <div 
          v-for="school in schools" 
          :key="school.id" 
          class="school-item"
          :class="{ active: activeSchoolId === school.id }"
          @click="focusSchool(school)"
        >
          <div class="school-color" :style="{ backgroundColor: school.color }"></div>
          <div class="school-info">
            <div class="school-name">{{ school.name }}</div>
            <div class="school-status">
              <el-tag :type="school.communities?.length > 0 ? 'success' : 'info'" size="small">
                {{ school.communities?.length > 0 ? `${school.communities.length}个小区` : '未绘制' }}
              </el-tag>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="loading-mask" v-if="loading">
      <el-icon class="is-loading" :size="40"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { schoolApi } from '@/api'
import type { School } from '@/types'

declare const AMap: any

const router = useRouter()
const mapContainer = ref<HTMLElement | null>(null)
const schools = ref<School[]>([])
const loading = ref(true)
const activeSchoolId = ref<number | null>(null)
const listVisible = ref(false)

let map: any = null
let polygons: any[] = []
let markers: any[] = []
let infoWindow: any = null

const AMAP_KEY = '11280b7f874f195dd2edf188a10f8429'

const initMap = () => {
  map = new AMap.Map('map', {
    zoom: 12,
    center: [121.78, 39.05],
    mapStyle: 'amap://styles/normal'
  })

  infoWindow = new AMap.InfoWindow({
    isCustom: true,
    autoMove: true,
    offset: new AMap.Pixel(0, -40)
  })
}

const loadSchools = async () => {
  try {
    const { data } = await schoolApi.getAll()
    schools.value = data
    renderMap()
  } catch (error) {
    ElMessage.error('加载学校数据失败')
  } finally {
    loading.value = false
  }
}

const renderMap = () => {
  polygons.forEach(p => map.remove(p))
  markers.forEach(m => map.remove(m))
  polygons = []
  markers = []

  schools.value.forEach(school => {
    if (school.communities && school.communities.length > 0) {
      school.communities.forEach(community => {
        try {
          const coords = JSON.parse(community.coordinates)
          if (coords.length >= 3) {
            const path = coords.map((c: number[]) => new AMap.LngLat(c[0], c[1]))
            
            const polygon = new AMap.Polygon({
              path: path,
              strokeColor: school.color,
              strokeWeight: 2,
              strokeOpacity: 0.8,
              fillColor: school.color,
              fillOpacity: 0.3,
              extData: {
                schoolId: school.id,
                communityName: community.name
              }
            })

            polygon.on('click', () => showSchoolInfo(school))
            polygon.on('mouseover', () => {
              polygon.setOptions({ fillOpacity: 0.5 })
            })
            polygon.on('mouseout', () => {
              polygon.setOptions({ fillOpacity: 0.3 })
            })

            map.add(polygon)
            polygons.push(polygon)
          }
        } catch (e) {
          console.error('解析小区坐标失败:', community.name, e)
        }
      })
    }

    if (school.longitude && school.latitude) {
      const marker = new AMap.Marker({
        position: [school.longitude, school.latitude],
        title: school.name,
        anchor: 'bottom-center'
      })

      marker.on('click', () => showSchoolInfo(school))
      marker.on('mouseover', () => showSchoolInfo(school))
      marker.on('mouseout', () => infoWindow.close())

      map.add(marker)
      markers.push(marker)
    }
  })
}

const showSchoolInfo = (school: School) => {
  activeSchoolId.value = school.id
  
  const communityCount = school.communities?.length || 0
  
  const content = `
    <div class="info-window">
      <div class="info-title">${school.name}</div>
      <div class="info-content">
        ${school.address ? `<p><strong>地址：</strong>${school.address}</p>` : ''}
        ${school.phone ? `<p><strong>电话：</strong>${school.phone}</p>` : ''}
        ${school.description ? `<p><strong>简介：</strong>${school.description}</p>` : ''}
        ${communityCount > 0 ? `<p><strong>小区数量：</strong>${communityCount}个</p>` : ''}
      </div>
    </div>
  `
  
  infoWindow.setContent(content)
  
  if (school.longitude && school.latitude) {
    infoWindow.open(map, [school.longitude, school.latitude])
  } else if (school.communities && school.communities.length > 0) {
    const allCoords: number[][] = []
    school.communities.forEach(c => {
      try {
        const coords = JSON.parse(c.coordinates)
        allCoords.push(...coords)
      } catch (e) {}
    })
    if (allCoords.length > 0) {
      const center = getPolygonCenter(allCoords)
      infoWindow.open(map, center)
    }
  }
}

const getPolygonCenter = (coords: number[][]): [number, number] => {
  let sumLng = 0
  let sumLat = 0
  coords.forEach(c => {
    sumLng += c[0]
    sumLat += c[1]
  })
  return [sumLng / coords.length, sumLat / coords.length]
}

const focusSchool = (school: School) => {
  if (school.longitude && school.latitude) {
    map.setCenter([school.longitude, school.latitude])
    map.setZoom(15)
    showSchoolInfo(school)
  } else if (school.communities && school.communities.length > 0) {
    const allCoords: number[][] = []
    school.communities.forEach(c => {
      try {
        const coords = JSON.parse(c.coordinates)
        allCoords.push(...coords)
      } catch (e) {}
    })
    if (allCoords.length > 0) {
      const center = getPolygonCenter(allCoords)
      map.setCenter(center)
      map.setZoom(14)
      showSchoolInfo(school)
    }
  } else {
    ElMessage.warning('该学校尚未定位')
  }
}

const goToAdmin = () => {
  router.push('/admin')
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
    initMap()
    await loadSchools()
  } catch (error) {
    ElMessage.error('地图初始化失败，请检查网络连接')
    loading.value = false
  }
})

onUnmounted(() => {
  if (map) {
    map.destroy()
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}

#map {
  width: 100%;
  height: 100%;
}

.map-header {
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 100;
  pointer-events: none;
}

.map-header h1 {
  background: white;
  padding: 15px 25px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  font-size: 20px;
  color: #303133;
  pointer-events: auto;
}

.map-header .el-button {
  pointer-events: auto;
}

.school-list-toggle {
  position: absolute;
  top: 80px;
  right: 20px;
  background: white;
  padding: 12px 15px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #303133;
  transition: background-color 0.2s;
}

.school-list-toggle:hover {
  background-color: #f5f7fa;
}

.toggle-arrow {
  transition: transform 0.3s;
  font-size: 16px;
}

.toggle-arrow.expanded {
  transform: rotate(90deg);
}

.school-list {
  position: absolute;
  top: 130px;
  right: 20px;
  width: 280px;
  max-height: calc(100% - 150px);
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.school-list-content {
  flex: 1;
  overflow-y: auto;
}

.school-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.school-item:hover {
  background-color: #f5f7fa;
}

.school-item.active {
  background-color: #ecf5ff;
}

.school-color {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  margin-right: 12px;
  flex-shrink: 0;
}

.school-info {
  flex: 1;
  min-width: 0;
}

.school-name {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.school-status {
  display: flex;
  align-items: center;
}

.loading-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 200;
}

.loading-mask span {
  margin-top: 15px;
  color: #606266;
}
</style>

<style>
.info-window {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  max-width: 300px;
}

.info-title {
  padding: 15px;
  border-bottom: 1px solid #ebeef5;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.info-content {
  padding: 15px;
}

.info-content p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.info-content p:last-child {
  margin-bottom: 0;
}
</style>
