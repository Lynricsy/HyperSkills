'use client'

import { db } from '@/lib/db'

type Props = { userId: string }

export default async function Summary({ userId }: Props) {
  const user = await db.user.findUnique({ where: { id: userId } })
  const invoices = await db.invoice.findMany({ where: { userId } })
  const settings = await db.settings.findUnique({ where: { userId } })

  return (
    <section>
      <h2>{user?.name}</h2>
      <p>{invoices.length} invoices</p>
      <p>Currency: {settings?.currency}</p>
    </section>
  )
}
