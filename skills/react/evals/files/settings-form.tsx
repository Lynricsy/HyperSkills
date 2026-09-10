'use client'

import { useState } from 'react'
import { Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'

export function SettingsForm() {
  const [plan, setPlan] = useState('monthly')
  const [email, setEmail] = useState('')
  const invalid = email.length > 0 && !email.includes('@')

  return (
    <Card className="bg-blue-50 text-blue-900 font-bold">
      <CardContent>
        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="text-gray-600">
              Email
            </label>
            <Input
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={`border ${invalid ? 'border-red-500' : 'border-gray-300'}`}
            />
            {invalid ? <p className="text-red-600">Invalid email.</p> : null}
          </div>

          <div className="flex space-x-2">
            {['monthly', 'yearly'].map((option) => (
              <Button
                key={option}
                variant={plan === option ? 'default' : 'outline'}
                onClick={() => setPlan(option)}
              >
                {option}
              </Button>
            ))}
          </div>

          <div className="relative">
            <Input placeholder="Search invoices…" className="pr-10" />
            <Button className="absolute right-0 top-0 z-50 w-10 h-10" size="icon">
              <Search className="mr-2 size-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
