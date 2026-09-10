import { db } from '@/lib/db'
import { createProduct } from './product-actions'

export default async function ProductsPage() {
  const products = await db.product.findMany({ orderBy: { name: 'asc' } })

  return (
    <main>
      <form action={createProduct}>
        <input name="name" required />
        <input name="priceCents" type="number" required />
        <button type="submit">Add</button>
      </form>
      <ul>
        {products.map((product) => (
          <li key={product.id}>{product.name}</li>
        ))}
      </ul>
    </main>
  )
}
