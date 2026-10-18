<template>
  <div class="contacts">
    <!-- Stats -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.contacts || 0 }}</div>
              <div class="stat-label">Total Contacts</div>
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
              <el-icon size="28"><Phone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ phoneCount }}</div>
              <div class="stat-label">With Phone</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Message /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ emailCount }}</div>
              <div class="stat-label">With Email</div>
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
          <el-input v-model="filters.name" placeholder="Name" style="width: 150px;" />
          <el-input v-model="filters.phone" placeholder="Phone" style="width: 150px;" />
          <el-button type="primary" @click="loadContacts">Search</el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </div>
      </div>
      
      <el-table :data="contactsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="Device UUID" width="250" show-overflow-tooltip />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="phone" label="Phone" />
        <el-table-column prop="email" label="Email" />
        <el-table-column prop="address" label="Address" />
        <el-table-column prop="created_at" label="Captured At" width="180" />
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
import { User, Iphone, Phone, Message } from '@element-plus/icons-vue'

const contactsData = ref([])
const loading = ref(false)
const stats = ref({})

const filters = reactive({
  device_uuid: '',
  name: '',
  phone: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const phoneCount = computed(() => contactsData.value.filter(item => item.phone).length)
const emailCount = computed(() => contactsData.value.filter(item => item.email).length)

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

async function loadContacts() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.name) params.append('name', filters.name)
    if (filters.phone) params.append('phone', filters.phone)
    
    const response = await axios.get(`/api/exfil/contacts?${params}`)
    contactsData.value = response.data
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
    loadContacts()
    loadStats()
  } catch (error) {
    console.error('Delete failed:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.name = ''
  filters.phone = ''
  loadContacts()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadContacts()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadContacts()
}

onMounted(() => {
  loadStats()
  loadContacts()
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