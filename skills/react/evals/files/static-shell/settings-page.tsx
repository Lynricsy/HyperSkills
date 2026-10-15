import { readFile } from "node:fs/promises"
import path from "node:path"

import { getUsage } from "@/lib/billing"
import { PlanCard } from "./plan-card"
import { UsageTable } from "./usage-table"

// data/plan-limits.json is edited by the billing team on the running servers
// (mounted volume) when limits change; we do not redeploy for it.
async function getPlanLimits() {
  const file = path.join(process.cwd(), "data/plan-limits.json")
  return JSON.parse(await readFile(file, "utf8")) as Record<string, number>
}

export default async function TeamSettingsPage({
  params,
}: PageProps<"/teams/[team]/settings">) {
  const { team } = await params
  const [limits, usage] = await Promise.all([getPlanLimits(), getUsage(team)])

  return (
    <section className="flex flex-col gap-6">
      <PlanCard limits={limits} />
      <UsageTable usage={usage} limits={limits} />
    </section>
  )
}
