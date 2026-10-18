<template>
  <div class="users">
    <el-card>
      <el-button type="primary" @click="showAddDialog = true" style="margin-bottom: 20px;">
        Add User
      </el-button>

      <el-table :data="users" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="Username" width="150" />
        <el-table-column prop="role" label="Role" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
              {{ scope.row.role === 'admin' ? 'Admin' : 'Operator' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created At" width="180" />
        <el-table-column prop="last_login" label="Last Login" width="180" />
        <el-table-column label="Actions" width="150">
          <template #default="scope">
            <el-button size="small" @click="editUser(scope.row)">Edit</el-button>
            <el-button size="small" type="danger" @click="deleteUser(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog :title="editingUser ? 'Edit User' : 'Add User'" v-model="showAddDialog">
      <el-form :model="userForm" ref="userFormRef" label-width="80px">
        <el-form-item label="Username" prop="username">
          <el-input v-model="userForm.username" placeholder="Enter username" />
        </el-form-item>
        <el-form-item label="Password" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="Enter password" />
        </el-form-item>
        <el-form-item label="Role" prop="role">
          <el-select v-model="userForm.role">
            <el-option label="Admin" value="admin" />
            <el-option label="Operator" value="operator" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveUser">OK</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const users = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const userFormRef = ref(null)
const editingUser = ref(null)

const userForm = reactive({
  username: '',
  password: '',
  role: 'operator'
})

async function loadUsers() {
  loading.value = true
  try {
    const response = await axios.get('/api/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

function editUser(user) {
  editingUser.value = user
  userForm.username = user.username
  userForm.password = ''
  userForm.role = user.role
  showAddDialog.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await axios.put(`/api/users/${editingUser.value.id}`, userForm)
    } else {
      await axios.post('/api/users', userForm)
    }
    showAddDialog.value = false
    editingUser.value = null
    userForm.username = ''
    userForm.password = ''
    userForm.role = 'operator'
    loadUsers()
  } catch (error) {
    console.error('Failed to save user:', error)
    alert(error.response?.data?.detail || 'Save failed')
  }
}

async function deleteUser(user) {
  if (user.role === 'admin') {
    alert('Cannot delete admin')
    return
  }
  if (!confirm(`Delete user ${user.username}?`)) return
  try {
    await axios.delete(`/api/users/${user.id}`)
    loadUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
    alert(error.response?.data?.detail || 'Delete failed')
  }
}

loadUsers()
</script>
