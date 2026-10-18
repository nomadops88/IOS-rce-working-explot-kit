<template>
  <div class="command-history">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="Device UUID" style="width: 250px;" />
        <el-input v-model="filters.command" placeholder="Command keyword" style="width: 200px;" />
        <el-select v-model="filters.status" placeholder="Status">
          <el-option label="All" value="" />
          <el-option label="Pending" value="pending" />
          <el-option label="Executing" value="executing" />
          <el-option label="Completed" value="completed" />
          <el-option label="Failed" value="failed" />
        </el-select>
        <el-button type="primary" @click="loadCommands">Search</el-button>
        <el-button @click="resetFilters">Reset</el-button>
        <div class="action-buttons">
          <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
            Batch Delete ({{ selectedIds.length }})
          </el-button>
          <el-button type="danger" @click="clearAll">Clear All</el-button>
        </div>
      </div>
      
      <el-table :data="commandsData" border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="Device UUID" width="250" />
        <el-table-column prop="command" label="Command" show-overflow-tooltip />
        <el-table-column prop="status" label="Status" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusName(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="output" label="Output" show-overflow-tooltip width="300">
          <template #default="scope">
            <el-button size="small" @click="showOutput(scope.row)">View</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created At" width="180" />
        <el-table-column prop="executed_at" label="Executed At" width="180" />
        <el-table-column label="Actions" width="150">
          <template #default="scope">
            <el-button size="small" @click="retryCommand(scope.row.id)" v-if="scope.row.status !== 'pending'">Retry</el-button>
            <el-button size="small" type="danger" @click="deleteCommand(scope.row.id)">Delete</el-button>
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
    
    <el-dialog title="Command Output" v-model="outputDialogVisible" width="60%">
      <pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{{ currentOutput }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'
import { formatDateTime, formatStatus } from '../utils'

const commandsData = ref([])
const loading = ref(false)
const outputDialogVisible = ref(false)
const currentOutput = ref('')
const selectedIds = ref([])

const filters = reactive({
  device_uuid: '',
  command: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getStatusType(status) {
  return formatStatus(status).type
}

function getStatusName(status) {
  return formatStatus(status).label
}

function showOutput(row) {
  currentOutput.value = row.output || 'No output'
  outputDialogVisible.value = true
}

function handleSelectionChange(val) {
  selectedIds.value = val.map(item => item.id)
}

async function loadCommands() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.command) params.append('command', filters.command)
    if (filters.status) params.append('status', filters.status)
    
    const response = await axios.get(`/api/commands?${params}`)
    commandsData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load data:', error)
  } finally {
    loading.value = false
  }
}

async function retryCommand(id) {
  try {
    await axios.post(`/api/commands/${id}/retry`)
    loadCommands()
  } catch (error) {
    console.error('Retry failed:', error)
  }
}

async function deleteCommand(id) {
  if (!confirm('Delete this command?')) return
  try {
    await axios.delete(`/api/commands/${id}`)
    loadCommands()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) return
  if (!confirm(`Delete ${selectedIds.value.length} selected commands?`)) return
  try {
    await axios.delete('/api/commands/batch', { data: { ids: selectedIds.value } })
    selectedIds.value = []
    loadCommands()
  } catch (error) {
    console.error('Batch delete failed:', error)
  }
}

async function clearAll() {
  if (!confirm('Clear all commands? This cannot be undone!')) return
  try {
    await axios.delete('/api/commands/clear')
    selectedIds.value = []
    loadCommands()
  } catch (error) {
    console.error('Clear failed:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.command = ''
  filters.status = ''
  loadCommands()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadCommands()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadCommands()
}

loadCommands()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
  align-items: center;
}

.action-buttons {
  margin-left: auto;
  display: flex;
  gap: 10px;
}
</style>