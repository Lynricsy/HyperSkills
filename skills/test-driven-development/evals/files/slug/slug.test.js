import { test } from 'node:test';
import assert from 'node:assert/strict';

import { toSlug } from './slug.js';

test('toSlug lowercases and joins words with hyphens', () => {
  assert.equal(toSlug('Release Notes'), 'release-notes');
});

test('toSlug keeps digits', () => {
  assert.equal(toSlug('Chapter 3'), 'chapter-3');
});
