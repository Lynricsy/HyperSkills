// app/orders/page.tsx
import { Suspense } from 'react'
import { OrderTable } from './_components/order-table'
import { OrdersSkeleton } from './_components/orders-skeleton'

// The database driver needs Node APIs, so pin the route to Node.js.
export const runtime = 'nodejs'

export default function OrdersPage() {
  return (
    <main>
      <h1>Orders</h1>
      <Suspense fallback={<OrdersSkeleton />}>
        <OrderTable />
      </Suspense>
    </main>
  )
}
