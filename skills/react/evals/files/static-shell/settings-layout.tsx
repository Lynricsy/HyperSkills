import { cookies } from "next/headers"
import { forbidden } from "next/navigation"

import { SettingsNav } from "./settings-nav"
import { getMembership } from "@/lib/auth"

export default async function TeamSettingsLayout({
  children,
  params,
}: LayoutProps<"/teams/[team]/settings">) {
  const { team } = await params
  const session = (await cookies()).get("session")?.value
  const membership = await getMembership(session, team)

  // Integrations and our uptime checks treat a 403 on this URL as
  // "not a member"; a 200 means the settings page is reachable.
  if (!membership || membership.role !== "admin") {
    forbidden()
  }

  return (
    <div className="grid grid-cols-[220px_1fr] gap-8">
      <SettingsNav team={team} />
      <main>
        <h1 className="text-2xl font-semibold">Team settings</h1>
        {children}
      </main>
    </div>
  )
}
