<template>
  <div>
    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item>
        <el-button type="success" @click="openDialog()"><el-icon><Plus /></el-icon>新建套件</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="suites" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="套件名称" min-width="180" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="env" label="指定环境" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.env" size="small">{{ row.env }}</el-tag>
          <span v-else style="color: #999">跟随配置</span>
        </template>
      </el-table-column>
      <el-table-column prop="case_count" label="用例数" width="80" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openDialog(row)">编辑</el-button>
          <el-button size="small" type="primary" @click="handleRun(row)" :loading="row._running">执行</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top: 16px; justify-content: flex-end"
      v-model:current-page="page" :total="total" :page-size="20"
      layout="total, prev, pager, next" @current-change="loadData" />

    <!-- 新建/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑套件' : '新建套件'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="套件名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="指定环境">
          <el-select v-model="form.env" clearable placeholder="不选则跟随config.yaml" style="width: 100%">
            <el-option v-for="e in envs" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联用例">
          <el-select v-model="form.case_ids" multiple filterable style="width: 100%">
            <el-option v-for="c in allCases" :key="c.id" :label="`[${c.method}] ${c.name}`" :value="c.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getSuites, createSuite, updateSuite, deleteSuite, getCases, runTests, getEnvironments } from '../api'

const router = useRouter()
const suites = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const dialogVisible = ref(false)
const editingId = ref(null)
const form = ref({})
const allCases = ref([])
const envs = ref([])

const loadData = async () => {
  loading.value = true
  try {
    const res = await getSuites({ page: page.value, page_size: 20 })
    suites.value = res.data.map(s => ({ ...s, _running: false }))
    total.value = res.total
  } finally { loading.value = false }
}

const loadAllCases = async () => {
  const res = await getCases({ page: 1, page_size: 500 })
  allCases.value = res.data || []
}

const loadEnvs = async () => {
  try { const res = await getEnvironments(); envs.value = res.environments || [] } catch(e) {}
}

const openDialog = async (row) => {
  await loadAllCases()
  await loadEnvs()
  if (row) {
    editingId.value = row.id
    form.value = { name: row.name, description: row.description, env: row.env, case_ids: row.case_ids || [] }
  } else {
    editingId.value = null
    form.value = { name: '', description: '', env: '', case_ids: [] }
  }
  dialogVisible.value = true
}

const handleSave = async () => {
  if (editingId.value) {
    await updateSuite(editingId.value, form.value)
    ElMessage.success('更新成功')
  } else {
    await createSuite(form.value)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  loadData()
}

const handleRun = async (row) => {
  row._running = true
  try {
    const res = await runTests({ suite_id: row.id, trigger_type: 'manual' })
    ElMessage.success(res.message)
    router.push(`/executions/${res.data.id}`)
  } catch(e) { ElMessage.error('执行失败') }
  finally { row._running = false }
}

const handleDelete = async (id) => {
  await ElMessageBox.confirm('确定删除该套件？', '提示', { type: 'warning' })
  await deleteSuite(id)
  ElMessage.success('删除成功')
  loadData()
}

onMounted(loadData)
</script>
