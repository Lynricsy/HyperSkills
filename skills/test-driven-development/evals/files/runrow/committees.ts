// Committee codes shown on a pipeline run row.
// Retired codes must never come back: dashboards key historical data on them.

export const COMMITTEE_CODES = ['ARCH', 'SEC', 'PERF', 'A11Y', 'DOCS', 'RELEASE', 'INFRA', 'DATA'] as const;

export const RETIRED_CODES = ['QA', 'OPS'] as const;
