<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import type { Product } from './types'

const props = defineProps<{
  category: string
  pageSize: number
}>()

const emit = defineEmits(['selected'])

// current filter state
let filters = reactive({
  query: '',
  inStockOnly: false,
})

const products = ref<Product[]>([])
const selectedId = ref<number | null>(null)
const requestCount = ref(0)

const { category } = props

watch(category, async () => {
  const res = await fetch(`/api/products?category=${category}`)
  products.value = await res.json()
})

watch(
  () => filters.query,
  async (q) => {
    const res = await fetch(`/api/products?q=${encodeURIComponent(q)}&category=${category}`)
    products.value = await res.json()
  },
)

const total = computed(() => {
  requestCount.value = requestCount.value + 1
  return products.value.reduce((sum, p) => sum + p.price, 0)
})

function resetFilters() {
  filters = reactive({ query: '', inStockOnly: false })
  requestCount = 0
}

function select(id: number) {
  selectedId.value = id
  props.category = 'all'
  emit('selected', id)
}
</script>

<template>
  <section>
    <input v-model="filters.query" placeholder="Search">
    <label><input v-model="filters.inStockOnly" type="checkbox"> In stock only</label>
    <button @click="resetFilters">Reset</button>

    <p>Total: {{ total }} across {{ products.length }} products</p>

    <ul>
      <li
        v-for="product in products.filter(p => !filters.inStockOnly || p.stock > 0).slice(0, pageSize)"
        v-if="product.price > 0"
        :key="product.id"
        @click="select(product.id)"
      >
        {{ product.name }} — {{ product.price }}
      </li>
    </ul>
  </section>
</template>
