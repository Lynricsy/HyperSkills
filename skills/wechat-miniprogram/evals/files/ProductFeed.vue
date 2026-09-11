<script setup lang="ts">
// src/views/ProductFeed.vue — Vue 3 + Vite SPA, ships to our web CDN
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const items = ref<any[]>([])
const filter = reactive({ keyword: '', sort: 'default' })
const scrollTop = ref(0)
let io: IntersectionObserver | null = null

const visible = computed(() =>
  items.value
    .filter((i) => i.title.includes(filter.keyword))
    .sort((a, b) => (filter.sort === 'price' ? a.price - b.price : 0)),
)

function onScroll() {
  scrollTop.value = window.scrollY
  document.querySelectorAll('.card').forEach((el) => {
    const r = el.getBoundingClientRect()
    el.classList.toggle('seen', r.top < window.innerHeight)
  })
}

onMounted(async () => {
  window.addEventListener('scroll', onScroll)
  const res = await fetch('/api/feed')
  items.value = await res.json()
  io = new IntersectionObserver(() => {})
  document.querySelectorAll('.card').forEach((el) => io!.observe(el))
})

onUnmounted(() => window.removeEventListener('scroll', onScroll))

function open(id: string) {
  router.push({ name: 'detail', params: { id } })
}
</script>

<template>
  <div class="feed">
    <input v-model="filter.keyword" placeholder="搜索" />
    <div v-for="(item, i) in visible" :key="i" class="card" @click="open(item.id)">
      <img :src="item.cover" />
      <h3>{{ item.title }}</h3>
      <span>¥{{ (item.priceCents / 100).toFixed(2) }}</span>
    </div>
  </div>
</template>

<style scoped>
.feed { display: grid; gap: 12px; }
.card { contain: content; }
</style>
