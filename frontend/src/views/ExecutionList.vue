<template>
  <div>
    <el-form :inline="true" style="margin-bottom: 16px">
      <el-form-item>
        <el-button type="primary" @click="handleRunAll" :loading="runningAll">
          <el-icon><VideoPlay /></el-icon>全量执行
        </el-button>
      </el-form-item>
      <el-form-item>
        <el-button @click="loadData"><el-icon><Refresh /></el-icon>刷新</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="records" border stripe v-loading="loading">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="env" label="环境" width="100">
        <template #default="{ row }"><el-tag size="small">{{ row.env }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="trigger_type" label="触发方式" width="100">
        <template #default="{ row }">
          <el-tag :type="row.trigger_type === 'manual' ? '' : row.trigger_type === 'scheduled' ? 'warning' : 'info'" size="small">
            {{ { manual: '手动', scheduled: '定时', ci: 'CI' }[row.trigger_type] || row.trigger_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusColor(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="结果" width="200">
        <template #default="{ row }">
          <span style="color: #67c23a">通过 {{ row.passed }}</span> /
          <span style="color: #f56c6c">失败 {{ row.failed }}</span> /
          <span style="color: #e6a23c">异常 {{ row.error }}</span> /
          共 {{ row.total }}
        </template>
      </el-table-column>
      <el-table-column prop="duration" label="耗时" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="170" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push(`/executions/${row.id}`)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination style="margin-top: 16px; justify-content: flex-end"
      v-model:current-page="page" :total="total" :page-size="20"
      layout="total, prev, pager, next" @current-change="loadData" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getExecutions, runTests } from '../api'

const router = useRouter()
const records = ref([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const runningAll = ref(false)

const statusColor = (s) => ({ passed: 'success', failed: 'danger', error: 'warning', running: '', pending: 'info' }[s] || 'info')
const statusText = (s) => ({ passed: '通过', failed: '失败', error: '异常', running: '执行中', pending: '等待中' }[s] || s)

const loadData = async () => {
  loading.value = true
  try {
    const res = await getExecutions({ page: page.value, page_size: 20 })
    records.value = res.data; total.value = res.total
  } finally { loading.value = false }
}

const handleRunAll = async () => {
  runningAll.value = true
  try {
    const res = await runTests({ trigger_type: 'manual' })
    ElMessage.success(res.message)
    router.push(`/executions/${res.data.id}`)
  } catch(e) { ElMessage.error('触发失败') }
  finally { runningAll.value = false }
}

onMounted(loadData)
</script>
