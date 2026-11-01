// app/orders/_components/orders-skeleton.tsx
export function OrdersSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading orders" className="space-y-2">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="h-10 animate-pulse rounded bg-muted" />
      ))}
    </div>
  )
}
