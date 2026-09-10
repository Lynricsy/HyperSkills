import { useEffect, useMemo, useState } from 'react';

type Order = {
  id: string;
  customer: string;
  total: number;
  placedAt: string;
  status: 'pending' | 'shipped' | 'cancelled';
};

export function OrderTable({ orders }: { orders: Order[] }) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<'date' | 'total'>('date');
  const [expanded, setExpanded] = useState<string | null>(null);

  const rows = orders
    .filter((o) => o.customer.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) =>
      sort === 'total' ? b.total - a.total : b.placedAt.localeCompare(a.placedAt)
    );

  useEffect(() => {
    document.title = `Orders (${rows.length})`;
  });

  return (
    <div style={{ height: '100%', overflowY: 'auto' }}>
      <input value={query} onChange={(e) => setQuery(e.target.value)} />
      <button onClick={() => setSort(sort === 'date' ? 'total' : 'date')}>
        sort by {sort === 'date' ? 'total' : 'date'}
      </button>
      <table>
        <tbody>
          {rows.map((order) => (
            <Row
              key={order.id}
              order={order}
              expanded={expanded === order.id}
              onToggle={() => setExpanded(expanded === order.id ? null : order.id)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Row({
  order,
  expanded,
  onToggle,
}: {
  order: Order;
  expanded: boolean;
  onToggle: () => void;
}) {
  const money = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  });
  const history = useMemo(() => buildHistory(order), [order]);

  return (
    <tr onClick={onToggle}>
      <td>{order.customer}</td>
      <td>{money.format(order.total)}</td>
      <td>{order.status}</td>
      {expanded && <td>{history.join(' -> ')}</td>}
    </tr>
  );
}

function buildHistory(order: Order): string[] {
  const stages = ['created', 'paid', 'packed', 'shipped', 'delivered'];
  return stages.map((s) => `${s}@${order.placedAt}`);
}
