import { writable, derived } from 'svelte/store';

export const filters = writable({ showChart: true, onlyActive: false });

export const summary = derived(filters, ($filters) =>
	$filters.onlyActive ? 'active only' : 'everything'
);

export function toggleChart() {
	filters.update((f) => ({ ...f, showChart: !f.showChart }));
}
