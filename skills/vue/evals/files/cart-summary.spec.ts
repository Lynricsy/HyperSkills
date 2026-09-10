import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CartSummary from './CartSummary.vue'
import { useCartStore } from './useCartStore'

describe('CartSummary', () => {
  it('renders', () => {
    const wrapper = mount(CartSummary)
    expect(wrapper.html()).toMatchSnapshot()
  })

  it('has the right internal state', () => {
    const wrapper = mount(CartSummary)
    // @ts-expect-error reach into the instance
    expect(wrapper.vm.cart.pendingRequests).toBe(0)
  })

  it('adds a line', async () => {
    const store = useCartStore()
    store.addLine({ sku: 'A-1', qty: 1, unitPrice: 500 })
    expect(store.subtotal).toBe(500)
  })
})
