<template>
  <div class="command-scripts">
    <el-card>
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">New Script</el-button>
      </div>

      <el-table :data="scriptsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="Script Name" />
        <el-table-column prop="description" label="Description" />
        <el-table-column prop="command" label="Command" show-overflow-tooltip />
        <el-table-column prop="created_at" label="Created At" width="180" />
        <el-table-column label="Actions" width="200">
          <template #default="scope">
            <el-button size="small" @click="runScript(scope.row)">Run</el-button>
            <el-button size="small" @click="editScript(scope.row)">Edit</el-button>
            <el-button size="small" type="danger" @click="deleteScript(scope.row.id)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog :title="editMode ? 'Edit Script' : 'New Script'" v-model="dialogVisible" width="60%">
      <el-form :model="scriptForm" label-width="120px">
        <el-form-item label="Script Name">
          <el-input v-model="scriptForm.name" placeholder="Enter script name" />
        </el-form-item>
        <el-form-item label="Description">
          <el-input v-model="scriptForm.description" placeholder="Enter description" />
        </el-form-item>
        <el-form-item label="Command Content">
          <el-input v-model="scriptForm.command" type="textarea" :rows="5" placeholder="Enter command content" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveScript">OK</el-button>
      </template>
    </el-dialog>
    
    <el-dialog title="Select Devices to Run" v-model="runDialogVisible" width="50%">
      <el-select v-model="selectedDevices" multiple placeholder="Select Devices" style="width: 100%;">
        <el-option v-for="device in devices" :key="device.device_uuid" :label="device.device_uuid" :value="device.device_uuid" />
      </el-select>
      <template #footer>
        <el-button @click="runDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="executeScript">Execute</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const scriptsData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const runDialogVisible = ref(false)
const editMode = ref(false)
const currentScript = ref(null)
const devices = ref([])
const selectedDevices = ref([])

const scriptForm = reactive({
  name: '',
  description: '',
  command: ''
})

async function loadScripts() {
  loading.value = true
  try {
    const response = await axios.get('/api/commands/scripts')
    scriptsData.value = response.data
  } catch (error) {
    console.error('Failed to load scripts:', error)
  } finally {
    loading.value = false
  }
}

async function loadDevices() {
  try {
    const response = await axios.get('/api/devices?limit=100')
    devices.value = Array.isArray(response.data) ? response.data : (response.data.items || [])
  } catch (error) {
    console.error('Failed to load devices:', error)
  }
}

function showAddDialog() {
  editMode.value = false
  currentScript.value = null
  scriptForm.name = ''
  scriptForm.description = ''
  scriptForm.command = ''
  dialogVisible.value = true
}

function editScript(script) {
  editMode.value = true
  currentScript.value = script
  scriptForm.name = script.name
  scriptForm.description = script.description
  scriptForm.command = script.command
  dialogVisible.value = true
}

async function saveScript() {
  try {
    if (editMode.value) {
      await axios.put(`/api/commands/scripts/${currentScript.value.id}`, scriptForm)
    } else {
      await axios.post('/api/commands/scripts', scriptForm)
    }
    dialogVisible.value = false
    loadScripts()
  } catch (error) {
    console.error('Save failed:', error)
  }
}

async function deleteScript(id) {
  if (!confirm('Delete this script?')) return
  try {
    await axios.delete(`/api/commands/scripts/${id}`)
    loadScripts()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

function runScript(script) {
  currentScript.value = script
  loadDevices()
  runDialogVisible.value = true
}

async function executeScript() {
  if (selectedDevices.value.length === 0) {
    alert('Please select devices')
    return
  }
  try {
    for (const device_uuid of selectedDevices.value) {
      await axios.post(`/api/commands?device_uuid=${device_uuid}`, { command: currentScript.value.command })
    }
    runDialogVisible.value = false
    alert('Commands sent')
  } catch (error) {
    console.error('Execute failed:', error)
  }
}

loadScripts()
</script>

<style scoped>
.toolbar {
  margin-bottom: 20px;
}
</style>
