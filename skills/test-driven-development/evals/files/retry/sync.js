import { getJson } from "./client.js";
import { upsertAll } from "./store.js";

// Nightly job: pulls invoices changed since the last run and stores them.
export async function syncInvoices(baseUrl, { since }) {
  const page = await getJson(`${baseUrl}/invoices?since=${since}`);
  await upsertAll(page.items);
  return page.items.length;
}
