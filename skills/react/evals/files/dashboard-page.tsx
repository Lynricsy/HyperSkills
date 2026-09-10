'use client'

import { useEffect, useState } from 'react'
import { LineChart, BarChart, PieChart } from 'recharts'
import { MonacoEditor } from '@/components/monaco-editor'
import { Check, X, Menu, Search, Bell } from 'lucide-react'

type User = { id: string; name: string; plan: string }
type Order = { id: string; total: number; createdAt: string }

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null)
  const [orders, setOrders] = useState<Order[]>([])
  const [showEditor, setShowEditor] = useState(false)

  useEffect(() => {
    fetch('/api/user')
      .then((r) => r.json())
      .then(setUser)
  }, [])

  useEffect(() => {
    if (!user) return
    fetch(`/api/orders?userId=${user.id}`)
      .then((r) => r.json())
      .then(setOrders)
  }, [user])

  const Header = () => (
    <header className="flex items-center gap-2">
      <Menu />
      <span>{user?.name ?? 'Loading…'}</span>
      <Bell />
    </header>
  )

  const sorted = orders.sort((a, b) => b.total - a.total)

  return (
    <div>
      <Header />
      {orders.length && <span>{orders.length} orders</span>}
      <LineChart width={600} height={300} data={sorted} />
      <BarChart width={600} height={300} data={sorted} />
      <PieChart width={300} height={300} data={sorted} />
      <button onClick={() => setShowEditor(true)}>
        <Search /> Edit config
      </button>
      {showEditor ? <MonacoEditor value="{}" /> : null}
      <Check />
      <X />
    </div>
  )
}
