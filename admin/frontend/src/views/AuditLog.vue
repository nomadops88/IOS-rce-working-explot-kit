<template>
  <div class="audit-log">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.username" placeholder="Username" style="width: 150px;" />
        <el-select v-model="filters.action" placeholder="Action Type">
          <el-option label="All" value="" />
          <el-option label="Login" value="login" />
          <el-option label="Logout" value="logout" />
          <el-option label="Create" value="create" />
          <el-option label="Update" value="update" />
          <el-option label="Delete" value="delete" />
          <el-option label="Command" value="command" />
        </el-select>
        <el-date-picker v-model="filters.date" type="date" placeholder="Select Date" style="width: 180px;" />
        <el-button type="primary" @click="loadLogs">Search</el-button>
        <el-button @click="resetFilters">Reset</el-button>
      </div>
      
      <el-table :data="logsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="Username" width="150" />
        <el-table-column prop="action" label="Action" width="120">
          <template #default="scope">
            <el-tag :type="getActionType(scope.row.action)">{{ getActionName(scope.row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource" label="Resource" />
        <el-table-column prop="details" label="Details" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column prop="created_at" label="Time" width="180" />
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
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const logsData = ref([])
const loading = ref(false)

const filters = reactive({
  username: '',
  action: '',
  date: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getActionType(action) {
  const types = { 'login': 'success', 'logout': 'info', 'create': 'warning', 'update': 'info', 'delete': 'danger', 'command': 'warning' }
  return types[action] || 'info'
}

function getActionName(action) {
  const names = { 'login': 'Login', 'logout': 'Logout', 'create': 'Create', 'update': 'Update', 'delete': 'Delete', 'command': 'Command' }
  return names[action] || action
}

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.username) params.append('username', filters.username)
    if (filters.action) params.append('action', filters.action)
    if (filters.date) params.append('date', filters.date)
    
    const response = await axios.get(`/api/audit?${params}`)
    logsData.value = response.data
  } catch (error) {
    console.error('Failed to load data:', error)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.username = ''
  filters.action = ''
  filters.date = ''
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
</style>
