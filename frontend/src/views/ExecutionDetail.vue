<template>
  <div v-loading="loading">
    <el-page-header @back="$router.push('/executions')" style="margin-bottom: 20px">
      <template #content>
        <span>执行记录 #{{ execId }}</span>
        <el-tag :type="statusColor(exec.status)" style="margin-left: 12px">{{ statusText(exec.status) }}</el-tag>
      </template>
    </el-page-header>

    <!-- 概览卡片 -->
    <el-row :gutter="16" style="margin-bottom: 20px">
      <el-col :span="4"><el-statistic title="总用例" :value="exec.total" /></el-col>
      <el-col :span="4"><el-statistic title="通过" :value="exec.passed" value-style="color: #67c23a" /></el-col>
      <el-col :span="4"><el-statistic title="失败" :value="exec.failed" value-style="color: #f56c6c" /></el-col>
      <el-col :span="4"><el-statistic title="异常" :value="exec.error" value-style="color: #e6a23c" /></el-col>
      <el-col :span="4"><el-statistic title="耗时" :value="exec.duration || '-'" /></el-col>
      <el-col :span="4">
        <el-tag>{{ exec.env }}</el-tag>
        <el-tag :type="exec.trigger_type === 'manual' ? '' : 'warning'" style="margin-left: 4px">
          {{ { manual: '手动', scheduled: '定时', ci: 'CI' }[exec.trigger_type] }}
        </el-tag>
      </el-col>
    </el-row>

    <!-- 结果明细 -->
    <el-table :data="results" border stripe>
      <el-table-column prop="case_name" label="用例名称" min-width="180" show-overflow-tooltip />
      <el-table-column prop="method" label="方法" width="80">
        <template #default="{ row }"><el-tag :type="methodColor(row.method)" size="small">{{ row.method }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="path" label="路径" min-width="180" show-overflow-tooltip />
      <el-table-column prop="status" label="结果" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'passed' ? 'success' : row.status === 'failed' ? 'danger' : 'warning'" size="small">
            {{ { passed: '通过', failed: '失败', error: '异常' }[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="actual_status_code" label="实际状态码" width="100" />
      <el-table-column prop="duration_ms" label="耗时(ms)" width="90" />
      <el-table-column label="详情" width="80">
        <template #default="{ row }">
          <el-button v-if="row.error_message" size="small" type="danger" text @click="showError(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 错误详情弹窗 -->
    <el-dialog v-model="errorVisible" title="错误详情" width="600px">
      <pre style="white-space: pre-wrap; word-break: break-all; background: #f5f5f5; padding: 12px; border-radius: 4px; max-height: 400px; overflow: auto">{{ errorContent }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getExecution, getExecutionResults } from '../api'

const route = useRoute()
const execId = computed(() => route.params.id)
const loading = ref(false)
const exec = ref({})
const results = ref([])
const errorVisible = ref(false)
const errorContent = ref('')

const statusColor = (s) => ({ passed: 'success', failed: 'danger', error: 'warning', running: '', pending: 'info' }[s] || 'info')
const statusText = (s) => ({ passed: '通过', failed: '失败', error: '异常', running: '执行中', pending: '等待中' }[s] || s)
const methodColor = (m) => ({ GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }[m] || '')

const showError = (row) => {
  errorContent.value = row.error_message || row.actual_response || '无详细信息'
  errorVisible.value = true
}

const loadData = async () => {
  loading.value = true
  try {
    const [execRes, resultsRes] = await Promise.all([
      getExecution(execId.value),
      getExecutionResults(execId.value),
    ])
    exec.value = execRes.data || {}
    results.value = resultsRes.data || []
  } finally { loading.value = false }
}

onMounted(loadData)
</script>
