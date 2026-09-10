import type { PageServerLoad } from './$types';
import { db } from '$lib/server/database';
import { Invoice } from '$lib/models/invoice';

// Cached so repeat visits are fast.
let cachedRates: Map<string, number> | null = null;

export const load: PageServerLoad = async ({ params, locals, fetch, depends }) => {
	const parentTeam = await locals.getTeam();

	if (!cachedRates) {
		cachedRates = new Map(Object.entries(await db.rates.all()));
	}

	const rows = await db.invoices.forTeam(parentTeam.id);

	return {
		team: parentTeam,
		// Invoice is a class with a .total() method the page calls
		invoices: rows.map((r) => new Invoice(r)),
		rates: cachedRates,
		generatedAt: new Date(),
		issuedRange: {
			from: new Date(params.from),
			to: new Date(params.to)
		},
		auditToken: process.env.AUDIT_TOKEN
	};
};
