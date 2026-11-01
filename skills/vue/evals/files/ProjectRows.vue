<script setup lang="ts">
// app/components/ProjectRows.vue
interface Project {
  id: string
  name: string
  owner: string
  updatedAt: string
}

const props = defineProps<{ selectedId: string | null }>()
const emit = defineEmits<{ select: [id: string] }>()

const { data: projects, refresh } = await useFetch<Project[]>('/api/projects', {
  default: () => [],
})

// Poll every 30 s; refresh() replaces data.value with fresh objects from the API.
let timer: ReturnType<typeof setInterval> | undefined
onMounted(() => {
  timer = setInterval(() => refresh(), 30_000)
})
onBeforeUnmount(() => clearInterval(timer))

async function rename(project: Project) {
  const name = window.prompt('New name', project.name)
  if (!name) return
  await $fetch(`/api/projects/${project.id}`, { method: 'PATCH', body: { name } })
  await refresh()
}
</script>

<template>
  <ul class="projects">
    <li
      v-for="project in projects"
      :key="project.id"
      v-memo="[project.id, project.id === props.selectedId]"
      :class="{ selected: project.id === props.selectedId }"
      @click="emit('select', project.id)"
    >
      <strong>{{ project.name }}</strong>
      <span>{{ project.owner }}</span>
      <time :datetime="project.updatedAt">{{ project.updatedAt }}</time>
      <button type="button" @click.stop="rename(project)">
        Rename
      </button>
    </li>
  </ul>
</template>
