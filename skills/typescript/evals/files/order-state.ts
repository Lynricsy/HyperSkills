// src/orders/order-state.ts
export interface Order {
  id: string;
  customerId: string;
  isDraft: boolean;
  isSubmitted: boolean;
  isPaid: boolean;
  isShipped: boolean;
  isCancelled: boolean;
  paymentIntentId?: string;
  paidAt?: Date;
  trackingNumber?: string;
  shippedAt?: Date;
  cancellationReason?: string;
  refundAmount?: number;
}

export function describeOrder(order: Order): string {
  if (order.isCancelled) {
    return `Cancelled: ${order.cancellationReason}`;
  }
  if (order.isShipped) {
    return `Shipped with ${order.trackingNumber!}`;
  }
  if (order.isPaid) {
    return `Paid at ${order.paidAt!.toISOString()}`;
  }
  if (order.isSubmitted) {
    return "Awaiting payment";
  }
  return "Draft";
}

export function refundable(order: Order): boolean {
  return order.isPaid && !order.isCancelled && order.paymentIntentId !== undefined;
}

export function markShipped(order: Order, tracking: string): Order {
  return {
    ...order,
    isShipped: true,
    trackingNumber: tracking,
    shippedAt: new Date(),
  };
}

// Both ids are plain strings, so callers regularly pass them in the wrong slot
// and nothing complains until production.
export function transferOrder(orders: Order[], orderId: string, customerId: string): Order[] {
  const next: Order[] = [];
  for (const order of orders) {
    next.push(order.id === orderId ? { ...order, customerId } : order);
  }
  return next;
}
