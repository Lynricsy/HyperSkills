"use client";

import { useState } from "react";

interface Project {
  id: string;
  name: string;
  updatedAt: string;
  archived: boolean;
}

export function ProjectList({ projects, query }: { projects: Project[]; query: string }) {
  const [showArchived, setShowArchived] = useState(false);

  const visible = projects
    .filter((p) => (showArchived ? true : !p.archived))
    .filter((p) => p.name.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));

  return (
    <div>
      <button onClick={() => setShowArchived((v) => !v)}>
        {showArchived ? "Hide archived" : "Show archived"}
      </button>
      <ul>
        {visible.map((p) => (
          <li key={p.id}>
            {p.name} — {p.updatedAt}
          </li>
        ))}
      </ul>
      <p>{visible.length} projects</p>
    </div>
  );
}
