// src/routes/newsletter/+page.server.ts
import { fail } from '@sveltejs/kit';
import { subscribe } from '#lib/server/mailer.js';
import type { Actions } from './$types';

export const actions = {
	subscribe: async ({ request }) => {
		const data = await request.formData();
		const email = String(data.get('email') ?? '');

		if (!email.includes('@')) return fail(400, { email, invalid: true });

		await subscribe(email);
		return { subscribed: true };
	}
} satisfies Actions;
