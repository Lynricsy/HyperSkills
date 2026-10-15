type Order = { id: string; number: string; customer: string; status: 'syncing' | 'paid' | 'refunded' };

function SyncIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" role="img" aria-label="Syncing">
      <circle cx="8" cy="8" r="6" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="28 10">
        <animateTransform attributeName="transform" type="rotate" from="0 8 8" to="360 8 8"
                          dur="1s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}

export function OrderList({ orders }: { orders: Order[] }) {
  return (
    <table data-qa="orders-table">
      <tbody>
        {orders.map((order, i) => (
          <tr key={order.id} data-testid={`order-row-${i}`}>
            <td>{order.number}</td>
            <td>{order.customer}</td>
            <td>{order.status === 'syncing' ? <SyncIcon /> : order.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
