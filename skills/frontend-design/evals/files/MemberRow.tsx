// members/MemberRow.tsx — rendered in a 360px-wide settings side panel.
import { z } from 'zod';

export const memberSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(120),
  email: z.string().email().max(254),
  role: z.string().max(60).optional(),
  avatarUrl: z.string().url().optional(),
  projectCount: z.number().int().nonnegative(),
});
export type Member = z.infer<typeof memberSchema>;

export const demoMembers: Member[] = [
  { id: '6f1c…', name: 'Jane Doe', email: 'jane@acme.com', role: 'Designer', avatarUrl: '/a/jane.png', projectCount: 12 },
  { id: '8a2d…', name: 'Sam Lee', email: 'sam@acme.com', role: 'Engineer', avatarUrl: '/a/sam.png', projectCount: 4 },
];

function initials(name: string) {
  const parts = name.split(' ');
  return (parts[0][0] + (parts[1]?.[0] ?? '')).toUpperCase();
}

export function MemberRow({ member }: { member: Member }) {
  return (
    <li className="flex items-center gap-3 py-2">
      {member.avatarUrl ? (
        <img src={member.avatarUrl} alt="" className="h-8 w-8 rounded-full" />
      ) : (
        <span className="grid h-8 w-8 place-items-center rounded-full bg-slate-200">{initials(member.name)}</span>
      )}
      <div className="flex-1">
        <p className="font-medium">{member.name}</p>
        <p className="text-sm text-slate-500">{member.email} · {member.role ?? '—'}</p>
      </div>
      <span className="rounded bg-slate-100 px-2 text-xs">{member.projectCount} projects</span>
      <button aria-label={`Actions for ${member.name}`} className="h-8 w-8">⋯</button>
    </li>
  );
}

export function MemberList({ members }: { members: Member[] }) {
  return (
    <section>
      <h3>{members.length} members</h3>
      <ul>{members.map((m) => <MemberRow key={m.id} member={m} />)}</ul>
    </section>
  );
}
