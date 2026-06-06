import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 响应拦截器
api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err)
    return Promise.reject(err)
  }
)

// ========== 用例 ==========
export const getCases = (params) => api.get('/cases', { params })
export const getCase = (id) => api.get(`/cases/${id}`)
export const createCase = (data) => api.post('/cases', data)
export const updateCase = (id, data) => api.put(`/cases/${id}`, data)
export const deleteCase = (id) => api.delete(`/cases/${id}`)
export const batchCreateCases = (data) => api.post('/cases/batch', data)
export const getModules = () => api.get('/cases/modules/list')

// ========== 套件 ==========
export const getSuites = (params) => api.get('/suites', { params })
export const getSuite = (id) => api.get(`/suites/${id}`)
export const createSuite = (data) => api.post('/suites', data)
export const updateSuite = (id, data) => api.put(`/suites/${id}`, data)
export const deleteSuite = (id) => api.delete(`/suites/${id}`)

// ========== 执行 ==========
export const getExecutions = (params) => api.get('/executions', { params })
export const getExecution = (id) => api.get(`/executions/${id}`)
export const getExecutionResults = (id) => api.get(`/executions/${id}/results`)
export const runTests = (data) => api.post('/executions/run', data)

// ========== 系统 ==========
export const getEnvironments = () => api.get('/environments')
export const healthCheck = () => api.get('/health')

export default api
