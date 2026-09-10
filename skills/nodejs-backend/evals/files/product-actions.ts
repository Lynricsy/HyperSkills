'use server'

import { db } from '@/lib/db'

export async function createProduct(formData: FormData) {
  await db.product.create({
    data: {
      name: String(formData.get('name')),
      priceCents: Number(formData.get('priceCents')),
    },
  })
}
