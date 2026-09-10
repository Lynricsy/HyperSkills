<script setup lang="ts">
import { onMounted } from 'vue'
import { useCartStore } from './useCartStore'

const cart = useCartStore()
const { subtotal, isEmpty, lines } = cart

onMounted(() => {
  cart.loadFromServer('me')
})

function bump(sku: string) {
  cart.addLine({ sku, qty: 1, unitPrice: 0 })
}
</script>

<template>
  <aside>
    <p v-if="isEmpty">Your cart is empty.</p>
    <ul v-else>
      <li v-for="line in lines" :key="line.sku">
        {{ line.sku }} x{{ line.qty }}
        <button @click="bump(line.sku)">+1</button>
      </li>
    </ul>
    <strong>Subtotal: {{ subtotal }}</strong>
  </aside>
</template>
