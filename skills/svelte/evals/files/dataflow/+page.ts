import type { PageLoad } from './$types';
import { db } from '$lib/server/database';

export const load: PageLoad = async ({ data, parent, fetch }) => {
	const layout = await parent();
	const exchange = await fetch('/api/exchange-rates').then((r) => r.json());

	// admin flag lives in localStorage
	const isAdmin = localStorage.getItem('admin') === '1';

	const auditTrail = await db.audit.forTeam(data.team.id);

	return {
		...data,
		locale: layout.locale,
		exchange,
		isAdmin,
		auditTrail
	};
};
