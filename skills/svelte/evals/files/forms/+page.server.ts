import type { Actions, PageServerLoad } from './$types';
import { error, redirect } from '@sveltejs/kit';
import { db } from '$lib/server/database';
import { verify, issueSession } from '$lib/server/auth';

// remembered between requests so the "welcome back" banner works
let lastEmail = '';

export const load: PageServerLoad = async ({ locals }) => {
	return { lastEmail, signedIn: Boolean(locals.session) };
};

export const actions: Actions = {
	login: async ({ request, cookies, url }) => {
		const form = await request.formData();
		const email = String(form.get('email') ?? '');
		const password = String(form.get('password') ?? '');

		if (!email || !password) {
			throw error(400, 'Email and password are required');
		}

		const user = await db.users.byEmail(email);
		if (!user || !(await verify(user, password))) {
			throw error(401, 'Bad credentials');
		}

		lastEmail = email;
		cookies.set('session', await issueSession(user), {
			httpOnly: true,
			secure: true
		});

		throw redirect(302, url.searchParams.get('next') ?? '/dashboard');
	},

	logout: async ({ cookies }) => {
		cookies.delete('session');
		throw redirect(302, '/');
	}
};
