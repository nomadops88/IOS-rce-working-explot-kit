<template>
  <div class="logs">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.ip" placeholder="IP Address" style="width: 150px;" />
        <el-input v-model="filters.device_uuid" placeholder="Device UUID" style="width: 200px;" />
        <el-input v-model="filters.path" placeholder="Path" style="width: 200px;" />
        <el-select v-model="filters.log_type" placeholder="Log Type">
          <el-option label="All" value="" />
          <el-option label="iOS Device" value="ios" />
          <el-option label="Request" value="request" />
          <el-option label="Exfil" value="exfil" />
          <el-option label="Frontend" value="frontend" />
          <el-option label="API" value="api" />
        </el-select>
        <el-date-picker
          v-model="filters.start_time"
          type="datetime"
          placeholder="Start Time"
          style="width: 200px;"
        />
        <el-date-picker
          v-model="filters.end_time"
          type="datetime"
          placeholder="End Time"
          style="width: 200px;"
        />
        <el-button type="primary" @click="loadLogs">Search</el-button>
        <el-button @click="resetFilters">Reset</el-button>
      </div>
      
      <div class="action-bar">
        <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">Batch Delete</el-button>
        <el-button type="danger" @click="clearLogs">Clear Logs</el-button>
      </div>
      
      <el-table :data="logs" border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="timestamp" label="Time" width="180" />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column prop="device_uuid" label="Device UUID" width="200">
          <template #default="scope">
            <span v-if="scope.row.device_uuid">{{ scope.row.device_uuid }}</span>
            <span v-else style="color:#999">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="Method" width="80" />
        <el-table-column prop="path" label="Path" />
        <el-table-column prop="status_code" label="Status Code" width="100" />
        <el-table-column prop="content_length" label="Size" width="100" />
        <el-table-column prop="log_type" label="Type" width="100">
          <template #default="scope">
            <el-tag :type="getLogTypeTag(scope.row.log_type)">
              {{ getLogTypeText(scope.row.log_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_agent" label="User Agent" show-overflow-tooltip />
        <el-table-column label="Actions" width="100">
          <template #default="scope">
            <el-button size="small" @click="deleteLog(scope.row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const logs = ref([])
const loading = ref(false)
const selectedIds = ref([])

const route = useRoute()

const filters = reactive({
  ip: '',
  device_uuid: '',
  path: '',
  log_type: '',
  start_time: null,
  end_time: null
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

onMounted(() => {
  if (route.query.device_uuid) {
    filters.device_uuid = route.query.device_uuid
  }
})

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.ip) params.append('ip', filters.ip)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.path) params.append('path', filters.path)
    if (filters.log_type) params.append('log_type', filters.log_type)
    if (filters.start_time) params.append('start_time', filters.start_time.toISOString())
    if (filters.end_time) params.append('end_time', filters.end_time.toISOString())
    
    const response = await axios.get(`/api/logs?${params}`)
    logs.value = response.data
    pagination.total = response.data.length + ((pagination.page - 1) * pagination.size) + 1
  } catch (error) {
    console.error('Failed to load logs:', error)
  } finally {
    loading.value = false
  }
}

function getLogTypeTag(type) {
  const tags = {
    'ios': 'danger',
    'exfil': 'danger',
    'request': 'info',
    'frontend': 'warning',
    'api': 'success'
  }
  return tags[type] || 'info'
}

function getLogTypeText(type) {
  const texts = {
    'ios': 'iOS Device',
    'exfil': 'Exfil',
    'request': 'Request',
    'frontend': 'Frontend',
    'api': 'API'
  }
  return texts[type] || type
}

async function deleteLog(id) {
  await ElMessageBox.confirm('Delete this log?', 'Warning', {
    confirmButtonText: 'Confirm',
    cancelButtonText: 'Cancel',
    type: 'warning'
  })
  try {
    await axios.delete(`/api/logs/${id}`)
    ElMessage.success('Deleted')
    loadLogs()
  } catch (error) {
    console.error('Delete failed:', error)
    ElMessage.error('Delete failed')
  }
}

async function batchDelete() {
  await ElMessageBox.confirm(`Delete ${selectedIds.value.length} selected logs?`, 'Warning', {
    confirmButtonText: 'Confirm',
    cancelButtonText: 'Cancel',
    type: 'warning'
  })
  try {
    await axios.delete('/api/logs/batch', { data: { ids: selectedIds.value } })
    ElMessage.success(`Deleted ${selectedIds.value.length} logs`)
    loadLogs()
  } catch (error) {
    console.error('Batch delete failed:', error)
    ElMessage.error('Batch delete failed')
  }
}

async function clearLogs() {
  let msg = 'Clear all logs?'
  if (filters.device_uuid) msg = 'Clear all logs for this device?'
  await ElMessageBox.confirm(msg, 'Warning', {
    confirmButtonText: 'Confirm',
    cancelButtonText: 'Cancel',
    type: 'warning'
  })
  try {
    let url = '/api/logs/clear'
    if (filters.device_uuid) url += '?device_uuid=' + filters.device_uuid
    await axios.delete(url)
    ElMessage.success('Logs cleared')
    loadLogs()
  } catch (error) {
    console.error('Clear logs failed:', error)
    ElMessage.error('Clear logs failed')
  }
}

function handleSelectionChange(selections) {
  selectedIds.value = selections.map(item => item.id)
}

function resetFilters() {
  filters.ip = ''
  filters.device_uuid = ''
  filters.path = ''
  filters.log_type = ''
  filters.start_time = null
  filters.end_time = null
  loadLogs()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadLogs()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadLogs()
}

loadLogs()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}
</style>
