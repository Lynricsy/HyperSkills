<script setup lang="ts">
import { reactive, computed, watch } from 'vue'

const props = defineProps<{ initial: Filter[] }>()

interface Filter {
  field: string
  value: string
}

let state = reactive({
  filters: props.initial,
  query: '',
})

const active = computed(() => state.filters.filter((f) => f.value !== ''))

async function reload() {
  const fresh = await fetch('/api/filters').then((r) => r.json())
  // replace the whole thing with what the server sent
  state = reactive({ filters: fresh, query: state.query })
}

watch(
  () => state.query,
  (q) => {
    if (q.length > 2) reload()
  },
)
</script>

<template>
  <input v-model="state.query" />
  <ul>
    <li v-for="f in active" :key="f.field">{{ f.field }}: {{ f.value }}</li>
  </ul>
  <button @click="reload">Reload</button>
</template>
