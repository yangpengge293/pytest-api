<template>
  <div>
    <!-- 搜索栏 -->
    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item>
        <el-input v-model="keyword" placeholder="搜索用例名称" clearable @clear="loadData" @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item>
        <el-select v-model="moduleFilter" placeholder="模块筛选" clearable @change="loadData">
          <el-option v-for="m in modules" :key="m" :label="m" :value="m" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-select v-model="priorityFilter" placeholder="优先级" clearable @change="loadData">
          <el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData"><el-icon><Search /></el-icon>搜索</el-button>
        <el-button type="success" @click="openDialog()"><el-icon><Plus /></el-icon>新建用例</el-button>
      </el-form-item>
    </el-form>

    <!-- 用例列表 -->
    <el-table :data="cases" border stripe v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="用例名称" min-width="160" show-overflow-tooltip />
      <el-table-column prop="method" label="方法" width="80">
        <template #default="{ row }">
          <el-tag :type="methodColor(row.method)" size="small">{{ row.method }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="path" label="请求路径" min-width="180" show-overflow-tooltip />
      <el-table-column prop="expected_status" label="预期状态码" width="100" />
      <el-table-column prop="module" label="模块" width="100" />
      <el-table-column prop="priority" label="优先级" width="80">
        <template #default="{ row }">
          <el-tag :type="row.priority === 'P0' ? 'danger' : row.priority === 'P1' ? 'warning' : 'info'" size="small">
            {{ row.priority }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="启用" width="70">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <el-pagination
      style="margin-top: 16px; justify-content: flex-end"
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50]"
      layout="total, sizes, prev, pager, next"
      @size-change="loadData"
      @current-change="loadData"
    />

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用例' : '新建用例'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用例名称"><el-input v-model="form.name" /></el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="请求方法">
              <el-select v-model="form.method" style="width: 100%">
                <el-option v-for="m in ['GET','POST','PUT','DELETE','PATCH']" :key="m" :label="m" :value="m" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="16">
            <el-form-item label="请求路径"><el-input v-model="form.path" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="请求头">
          <el-input v-model="form.headers" type="textarea" :rows="2" placeholder='JSON格式，如：{"Authorization": "Bearer xxx"}' />
        </el-form-item>
        <el-form-item label="请求参数">
          <el-input v-model="form.body" type="textarea" :rows="3" placeholder='JSON格式，GET为query参数，POST为body' />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="预期状态码"><el-input-number v-model="form.expected_status" :min="100" :max="599" /></el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" style="width: 100%">
                <el-option v-for="p in ['P0','P1','P2','P3']" :key="p" :label="p" :value="p" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="所属模块"><el-input v-model="form.module" /></el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="预期响应">
          <el-input v-model="form.expected_fields" type="textarea" :rows="2" placeholder='JSON格式，如：{"id": 1}' />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCases, createCase, updateCase, deleteCase, getModules } from '../api'

const cases = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const keyword = ref('')
const moduleFilter = ref('')
const priorityFilter = ref('')
const modules = ref([])

const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const form = ref({})

const methodColor = (m) => ({ GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger', PATCH: 'info' }[m] || '')

const loadData = async () => {
  loading.value = true
  try {
    const res = await getCases({ page: page.value, page_size: pageSize.value, keyword: keyword.value, module: moduleFilter.value, priority: priorityFilter.value })
    cases.value = res.data
    total.value = res.total
  } finally { loading.value = false }
}

const loadModules = async () => {
  try { const res = await getModules(); modules.value = res.data || [] } catch(e) {}
}

const openDialog = (row) => {
  if (row) {
    editingId.value = row.id
    form.value = { ...row }
  } else {
    editingId.value = null
    form.value = { name: '', method: 'GET', path: '/', headers: '', body: '', expected_status: 200, expected_fields: '', module: '', priority: 'P1', is_active: true, sort_order: 0 }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  saving.value = true
  try {
    if (editingId.value) {
      await updateCase(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await createCase(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
    loadModules()
  } finally { saving.value = false }
}

const handleDelete = async (id) => {
  await ElMessageBox.confirm('确定删除该用例？', '提示', { type: 'warning' })
  await deleteCase(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(() => { loadData(); loadModules() })
</script>
