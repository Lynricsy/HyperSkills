import { COMMITTEE_CODES } from './committees.js';

/** How many badges fit on one run row. */
export const LIST_LIMIT = 10;

export function renderRunRow(id, errors, approvals) {
  return {
    id,
    errors: errors.slice(0, LIST_LIMIT),
    errorsTotal: errors.length,
    committees: COMMITTEE_CODES.filter((c) => approvals[c]).slice(0, LIST_LIMIT),
  };
}
