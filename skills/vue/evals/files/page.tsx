// app/reports/page.tsx — Next.js App Router
import { getOrganisation } from '@/lib/org'
import { getReports } from '@/lib/reports'
import { getBillingSummary } from '@/lib/billing'
import { ReportTable } from './report-table'

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: Promise<{ range?: string }>
}) {
  const { range } = await searchParams

  const org = await getOrganisation()
  const reports = await getReports(org.id, range ?? '30d')
  const billing = await getBillingSummary(org.id)

  return (
    <main>
      <h1>{org.name}</h1>
      <p>Plan: {billing.plan}</p>
      <ReportTable reports={reports} />
    </main>
  )
}
