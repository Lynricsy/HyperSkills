import { expect, test, vi } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import Counter from './Counter.svelte';

test('increments', async () => {
	render(Counter, { start: 0 });

	const button = page.getByRole('button', { name: 'Increment' });
	await button.click();

	await expect.element(button).toHaveTextContent('1');
});

test('starts from the given value', async () => {
	render(Counter, { start: 5 });

	await expect.element(page.getByRole('button', { name: 'Increment' })).toHaveTextContent('5');
});

test('saves the current count', async () => {
	const onsave = vi.fn();
	render(Counter, { start: 2, onsave });

	await page.getByText('Save').click();

	expect(onsave).toHaveBeenCalledWith(2);
});
