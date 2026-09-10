'use client'

import { memo, useEffect, useMemo, useState } from 'react'
import { buildSearchIndex, slugify } from '@/lib/search'

type Project = { id: string; name: string; updatedAt: number; tags: string[] }

const ProjectCard = memo(function ProjectCard({
  project,
  onOpen = () => {},
}: {
  project: Project
  onOpen?: (id: string) => void
}) {
  return (
    <li onClick={() => onOpen(project.id)}>
      {project.name} — {slugify(project.name)}
    </li>
  )
})

export function ProjectList({ projects }: { projects: Project[] }) {
  const [index, setIndex] = useState(buildSearchIndex(projects))
  const [query, setQuery] = useState('')
  const [matchCount, setMatchCount] = useState(0)

  const visible = useMemo(() => {
    const sorted = projects.sort((a, b) => b.updatedAt - a.updatedAt)
    return sorted.filter((p) => p.tags.includes('active'))
  }, [projects, query])

  useEffect(() => {
    setMatchCount(visible.length)
  }, [visible])

  const isBusy = useMemo(() => query.length > 0 && projects.length > 0, [query, projects])

  return (
    <div>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <span>{matchCount} matching</span>
      {isBusy ? <span>Searching…</span> : null}
      <ul>
        {visible.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </ul>
    </div>
  )
}
