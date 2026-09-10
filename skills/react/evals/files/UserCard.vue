<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{ userId: string }>()

const user = ref<{ name: string; email: string } | null>(null)
const loading = ref(false)

const initials = computed(() => user.value?.name.slice(0, 2).toUpperCase() ?? '')

watch(
  () => props.userId,
  async (id) => {
    loading.value = true
    const res = await fetch(`/api/users/${id}`)
    user.value = await res.json()
    loading.value = false
  },
  { immediate: true }
)
</script>

<template>
  <div class="card">
    <span v-if="loading">Loading…</span>
    <div v-else>
      <div class="avatar">{{ initials }}</div>
      <p>{{ user?.name }}</p>
      <p>{{ user?.email }}</p>
    </div>
  </div>
</template>

<style scoped>
.card {
  display: flex;
  gap: 12px;
}
</style>
