import { defineStore } from 'pinia'
import { computed, readonly, ref } from 'vue'

export interface CartLine {
  sku: string
  qty: number
  unitPrice: number
}

export const useCartStore = defineStore('cart', () => {
  const lines = ref<CartLine[]>([])
  const couponCode = ref('')
  // internal: never exposed to components
  const lastSyncedAt = ref<number | null>(null)
  const pendingRequests = ref(0)

  const subtotal = computed(() =>
    lines.value.reduce((sum, l) => sum + l.qty * l.unitPrice, 0),
  )

  const isEmpty = computed(() => lines.value.length === 0)

  async function loadFromServer(userId: string) {
    pendingRequests.value++
    const res = await fetch(`/api/cart/${userId}`)
    lines.value = await res.json()
    lastSyncedAt.value = Date.now()
    pendingRequests.value--
  }

  function addLine(line: CartLine) {
    const existing = lines.value.find(l => l.sku === line.sku)
    if (existing) {
      existing.qty += line.qty
      return
    }
    lines.value.push(line)
  }

  function applyCoupon(code: string) {
    couponCode.value = code
    lastSyncedAt.value = null
  }

  return {
    lines: readonly(lines),
    couponCode,
    subtotal,
    isEmpty,
    loadFromServer,
    addLine,
    applyCoupon,
  }
})
