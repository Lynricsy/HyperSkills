<script setup lang="ts">
// app/pages/dashboard.vue
const stats = await $fetch('/api/stats')

const theme = localStorage.getItem('theme') || 'light'

const { data: projects } = await useFetch('/api/projects')

function archive(id: string) {
  const hit = projects.value?.find(p => p.id === id)
  if (hit) {
    hit.archived = true
  }
}

const greeting = new Date().getHours() < 12 ? 'Good morning' : 'Good afternoon'
</script>

<template>
  <main :class="theme">
    <h1>{{ greeting }}</h1>
    <p>{{ stats.activeUsers }} active users · rendered at {{ new Date().toISOString() }}</p>

    <ProjectList :projects="projects ?? []" @archive="archive" />
    <ProjectQuota />
  </main>
</template>
