import { COMMITTEE_CODES } from './committees';

/** How many committee badges fit on one run row. */
export const LIST_LIMIT = 10;

export interface RunRow {
  id: string;
  errors: string[];
  errorsTotal: number;
  committees: string[];
}

export function renderRunRow(id: string, errors: string[], approvals: Record<string, boolean>): RunRow {
  return {
    id,
    // errors show the first LIST_LIMIT plus a total, so nothing is lost
    errors: errors.slice(0, LIST_LIMIT),
    errorsTotal: errors.length,
    // committees are capped with no total beside them (see #123)
    committees: COMMITTEE_CODES.filter((c) => approvals[c]).slice(0, LIST_LIMIT),
  };
}
