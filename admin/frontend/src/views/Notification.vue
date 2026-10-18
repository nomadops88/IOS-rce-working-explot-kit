<template>
  <div class="notification">
    <el-card>
      <div class="toolbar toolbar--with-switch">
        <div class="toolbar-left">
          <el-button @click="markAllRead">Mark All Read</el-button>
          <el-button type="danger" @click="clearAll">Clear All</el-button>
        </div>
        <div class="toolbar-right">
          <div class="notify-switch-row">
            <el-switch
              v-model="notifyEnabled"
              @change="handleNotifySwitchChange"
              @click.capture="onSwitchCaptureClick"
              :loading="permissionRequesting"
            />
            <span class="notify-switch-label">Browser Notifications</span>
            <el-tag size="small" :type="permissionTagType" effect="plain">
              {{ permissionText }}
            </el-tag>
            <el-button
              v-if="permission === 'default'"
              type="primary"
              size="small"
              plain
              @click="requestNotifyPermission"
              :loading="permissionRequesting"
            >Authorize Now</el-button>
            <el-button
              v-else-if="permission === 'denied'"
              type="warning"
              size="small"
              plain
              @click="openSiteSettingsHelp"
            >How to Enable</el-button>
          </div>
          <div class="notify-switch-row">
            <el-switch
              v-model="pageToastEnabled"
              @change="handlePageToastSwitchChange"
            />
            <span class="notify-switch-label">Page Toast Notifications</span>
            <el-tag size="small" type="success" effect="plain" v-if="pageToastEnabled">Enabled</el-tag>
            <el-tag size="small" type="info" effect="plain" v-else>Disabled</el-tag>
          </div>
          <div class="notify-hint" v-if="notifyEnabled && permission === 'default'">
            Click <b>Authorize Now</b> on the right, then click <b>Allow</b> in the browser popup to receive desktop alerts for new device connections and other events
          </div>
          <div class="notify-hint notify-hint--warn" v-else-if="notifyEnabled && permission === 'denied'">
            Permission denied by browser. Click "How to Enable", or set Notifications to Allow in the site settings (address bar icon) and refresh
          </div>
          <div class="notify-hint" v-if="!pageToastEnabled && notifyEnabled">
            Page toast notifications disabled — only browser system notifications will appear
          </div>
        </div>
      </div>

      <div v-if="totalCount !== null" class="list-summary">
        {{ totalCount }} notifications · {{ unreadCount }} unread
      </div>
      
      <div class="notification-list">
        <div 
          v-for="notification in notifications" 
          :key="notification.id" 
          class="notification-item"
          :class="{ 'read': notification.read }"
          @click="markRead(notification.id)"
        >
          <div class="notification-icon">
            <el-icon v-if="notification.type === 'device'"><Phone /></el-icon>
            <el-icon v-else-if="notification.type === 'exfil'"><FolderOpened /></el-icon>
            <el-icon v-else-if="notification.type === 'command'"><Monitor /></el-icon>
            <el-icon v-else><Bell /></el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-desc">{{ notification.description }}</div>
            <div class="notification-meta">
              <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
              <el-tag
                v-if="notification.related_device_uuid"
                size="small"
                effect="plain"
                type="info"
              >
                Device: {{ truncateUuid(notification.related_device_uuid) }}
              </el-tag>
            </div>
          </div>
          <div class="notification-status">
            <el-tag v-if="!notification.read" type="danger">Unread</el-tag>
          </div>
        </div>
        
        <div v-if="notifications.length === 0" class="empty-state">
          <el-icon size="48" style="color: #ccc;"><Bell /></el-icon>
          <p>No notifications</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Phone, FolderOpened, Monitor, Bell } from '@element-plus/icons-vue'

const LS_KEY = 'notify_enabled'
const LS_PAGE_TOAST_KEY = 'page_toast_enabled'

const notifications = ref([])
const totalCount = ref(null)
const unreadCount = ref(null)
const notifyEnabled = ref(localStorage.getItem(LS_KEY) === 'true')
const pageToastEnabled = ref(localStorage.getItem(LS_PAGE_TOAST_KEY) !== 'false')
const permissionRequesting = ref(false)

const permission = ref(
  (typeof window !== 'undefined' && 'Notification' in window) ? Notification.permission : 'unsupported'
)

let permissionInterval = null

function handlePushNotification(event) {
  const item = event && event.detail
  if (!item) return
  const existingId = typeof item.id === 'number' ? item.id : null
  if (existingId && notifications.value.some(n => n.id === existingId)) return
  notifications.value.unshift({
    id: item.id ?? Date.now(),
    title: item.title || '',
    description: item.description || '',
    type: item.type || item.category || 'info',
    read: false,
    created_at: item.created_at || new Date().toISOString(),
    related_device_uuid: item.related_device_uuid || null,
  })
  totalCount.value = (totalCount.value ?? notifications.value.length - 1) + 1
  unreadCount.value = (unreadCount.value ?? 0) + 1
}

onMounted(() => {
  loadNotifications()
  if ('Notification' in window) {
    permissionInterval = setInterval(() => {
      permission.value = Notification.permission
    }, 2000)
  }
  window.addEventListener('darksword:notification', handlePushNotification)
})

onBeforeUnmount(() => {
  if (permissionInterval) clearInterval(permissionInterval)
  window.removeEventListener('darksword:notification', handlePushNotification)
})

const permissionText = computed(() => {
  if (permission.value === 'granted') return 'Permission Granted'
  if (permission.value === 'denied') return 'Permission Denied'
  if (permission.value === 'default') return 'Not Authorized'
  return 'Not Supported'
})

const permissionTagType = computed(() => {
  if (permission.value === 'granted') return 'success'
  if (permission.value === 'denied') return 'danger'
  if (permission.value === 'default') return 'warning'
  return 'info'
})

function truncateUuid(uuid) {
  if (!uuid) return ''
  if (uuid.length <= 8) return uuid
  return uuid.slice(0, 8) + '...'
}

function fireTestNotification() {
  try {
    const n = new Notification('DarkSword notifications enabled ✅', {
      body: 'You will receive desktop notifications when new devices connect, access events occur, or important events happen (click to open notification center)',
      tag: 'darksword-notify-test-' + Date.now(),
      icon: '/favicon.ico'
    })
    if (n && typeof n.addEventListener === 'function') {
      n.addEventListener('click', () => {
        window.focus()
        n.close()
      })
    }
    setTimeout(() => n && n.close && n.close(), 7000)
  } catch (_) {}
}

function refreshPermission() {
  if ('Notification' in window) {
    permission.value = Notification.permission
  }
}

async function requestNotifyPermission(thenEnableSwitch = true) {
  if (!('Notification' in window)) {
    ElMessage.warning('This browser does not support desktop notifications')
    return false
  }
  refreshPermission()
  if (permission.value === 'granted') {
    if (thenEnableSwitch) {
      notifyEnabled.value = true
      localStorage.setItem(LS_KEY, 'true')
    }
    fireTestNotification()
    ElMessage.success('Notification permission ready')
    return true
  }
  if (permission.value === 'denied') {
    ElMessage.warning('Notification permission denied. Enable it in site settings (address bar icon) and refresh')
    return false
  }
  if (permissionRequesting.value) return false
  permissionRequesting.value = true
  try {
    const result = await Notification.requestPermission()
    permission.value = result
    if (result === 'granted') {
      if (thenEnableSwitch) {
        notifyEnabled.value = true
        localStorage.setItem(LS_KEY, 'true')
      }
      ElMessage.success('Notification permission granted. You will be alerted for new device connections and other events')
      fireTestNotification()
      return true
    } else if (result === 'denied') {
      ElMessage.warning('You clicked Deny — browser will not show notifications')
      return false
    } else {
      ElMessage.info('Notification permission not granted — notifications visible only in the list')
      return false
    }
  } catch (err) {
    console.error('Failed to request notification permission:', err)
    ElMessage.error('Failed to request notification permission')
    return false
  } finally {
    permissionRequesting.value = false
  }
}

function onSwitchCaptureClick() {
  if (!('Notification' in window)) return
  if (notifyEnabled.value === false) return
  if (permission.value === 'default') {
    requestNotifyPermission(false)
  }
}

function openSiteSettingsHelp() {
  const msg = 'In the address bar, click the site icon (🔒/⚠️), set Notifications to Allow, then refresh the page'
  ElMessageBox && typeof ElMessageBox.alert === 'function'
    ? ElMessageBox.alert(msg, 'How to Enable Browser Notifications', { confirmButtonText: 'OK' }).catch(() => {})
    : ElMessage.info(msg)
}

function handlePageToastSwitchChange(on) {
  localStorage.setItem(LS_PAGE_TOAST_KEY, on ? 'true' : 'false')
  if (on) {
    ElMessage.success('Page toast notifications enabled — new events will appear in the bottom right')
  } else {
    ElMessage.info('Page toast notifications disabled')
  }
}

async function handleNotifySwitchChange(on) {
  localStorage.setItem(LS_KEY, on ? 'true' : 'false')
  if (!on) {
    ElMessage.info('Browser notifications disabled')
    return
  }
  await requestNotifyPermission(true)
}

function mapNotification(item) {
  if (!item) return item
  return {
    id: item.id,
    title: item.title || '',
    description: item.description || item.message || '',
    type: item.type || item.category || 'info',
    read: item.read === true || item.is_read === 1 || item.is_read === true,
    created_at: item.created_at || item.timestamp || new Date().toISOString(),
    related_device_uuid: item.related_device_uuid || null,
    related_resource_type: item.related_resource_type || null,
    related_resource_id: item.related_resource_id || null
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('en-US')
}

async function loadNotifications() {
  try {
    const response = await axios.get('/api/notifications')
    const data = response.data
    const items = Array.isArray(data) ? data : (data?.items || [])
    notifications.value = items.map(mapNotification)
    if (!Array.isArray(data)) {
      totalCount.value = typeof data.total === 'number' ? data.total : items.length
      unreadCount.value = typeof data.unread_count === 'number' ? data.unread_count
        : items.filter(n => !n.read).length
    } else {
      totalCount.value = items.length
      unreadCount.value = items.filter(n => !n.read).length
    }
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

async function markRead(id) {
  try {
    await axios.put(`/api/notifications/${id}/read`)
    loadNotifications()
  } catch (error) {
    console.error('Mark read failed:', error)
    ElMessage.error('Mark read failed')
  }
}

async function markAllRead() {
  try {
    await axios.put('/api/notifications/read')
    ElMessage.success('All marked as read')
    loadNotifications()
  } catch (error) {
    console.error('Mark all read failed:', error)
    ElMessage.error('Mark all read failed')
  }
}

async function clearAll() {
  if (!confirm('Clear all notifications?')) return
  try {
    await axios.delete('/api/notifications')
    ElMessage.success('Notifications cleared')
    loadNotifications()
  } catch (error) {
    console.error('Clear failed:', error)
    ElMessage.error('Clear failed')
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.notify-switch-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notify-switch-label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.notify-hint {
  font-size: 12px;
  color: #606266;
  max-width: 360px;
  line-height: 1.5;
  padding: 6px 10px;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
}

.notify-hint--warn {
  background: #fdf6ec;
  color: #e6a23c;
}

.list-summary {
  margin-bottom: 14px;
  color: #606266;
  font-size: 13px;
  padding-left: 4px;
}

.notification-list {
  max-height: 600px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-item.read {
  opacity: 0.6;
}

.notification-icon {
  font-size: 24px;
  color: #409eff;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.notification-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
  white-space: pre-line;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.notification-status {
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #999;
}
</style>
