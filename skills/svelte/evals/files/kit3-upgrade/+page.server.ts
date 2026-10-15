// src/routes/account/[id]/+page.server.ts
import { error } from '@sveltejs/kit';
import { BILLING_API_KEY } from '$env/static/private';
import { db } from '$lib/server/db';
import type { Actions, PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ params, cookies }) => {
	const account = await db.account.find(params.id);
	if (!account) {
		error(404, { message: 'Account not found', code: 'NO_ACCOUNT' });
	}

	const invoices = await db.billing.invoices(account.id, BILLING_API_KEY);

	return {
		account: { id: account.id, name: account.name, plan: account.plan },
		invoices: invoices.map((i) => ({ id: i.id, total: i.total, issuedAt: i.issuedAt })),
		theme: cookies.get('theme') ?? 'light'
	};
};

export const actions: Actions = {
	theme: async ({ request, cookies }) => {
		const data = await request.formData();
		const theme = data.get('theme') === 'dark' ? 'dark' : 'light';
		cookies.set('theme', theme, { httpOnly: false, maxAge: 60 * 60 * 24 * 365 });
	}
};
