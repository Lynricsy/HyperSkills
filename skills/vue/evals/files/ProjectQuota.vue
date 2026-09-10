<script setup lang="ts">
// app/components/ProjectQuota.vue
const { data: projects } = await useFetch('/api/projects')

const config = useRuntimeConfig()

const used = computed(() => projects.value?.length ?? 0)
</script>

<template>
  <p>
    {{ used }} of {{ config.maxProjects }} projects used
    (billing account {{ config.stripeSecretKey ? 'connected' : 'missing' }})
  </p>
</template>
