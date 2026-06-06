<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside width="200px" style="background: #304156">
      <div style="color: #fff; text-align: center; padding: 20px; font-size: 16px; font-weight: bold">
        接口测试平台
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
      >
        <el-menu-item index="/cases">
          <el-icon><Document /></el-icon>
          <span>用例管理</span>
        </el-menu-item>
        <el-menu-item index="/suites">
          <el-icon><FolderOpened /></el-icon>
          <span>套件管理</span>
        </el-menu-item>
        <el-menu-item index="/executions">
          <el-icon><VideoPlay /></el-icon>
          <span>执行记录</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容 -->
    <el-container>
      <el-header style="border-bottom: 1px solid #e6e6e6; display: flex; align-items: center; justify-content: space-between">
        <span style="font-size: 18px; font-weight: bold">{{ $route.meta.title || '接口测试平台' }}</span>
        <el-tag type="success" size="small">环境: {{ activeEnv }}</el-tag>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getEnvironments } from './api'

const activeEnv = ref('')

onMounted(async () => {
  try {
    const res = await getEnvironments()
    activeEnv.value = res.active_env || ''
  } catch (e) {
    console.error(e)
  }
})
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.el-menu { border-right: none; }
</style>
