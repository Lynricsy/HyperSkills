# Incident: demo project overspend (project `acme-summarizer-demo`, number 481516234200)

Billing account 01A2B3-C4D5E6-F7A8B9, self-serve, direct with Google (no reseller).

## What runs in the project

| Resource | Notes |
|---|---|
| Cloud Run service `summarizer` (us-central1) | public, `max-instances` unset, request-based billing |
| Gemini on Vertex AI (Gemini Enterprise Agent Platform) | called by `summarizer`, pay-as-you-go |
| Cloud SQL for PostgreSQL `demo-db` | db-custom-2-8192, HA off |
| Cloud Storage bucket `acme-summarizer-uploads` | Standard, ~200 GB |

## Existing budget

```bash
gcloud billing budgets describe 6b1f0c3e-... --billing-account=01A2B3-C4D5E6-F7A8B9
displayName: demo-project
amount: { specifiedAmount: { units: '500', currencyCode: USD } }
budgetFilter: { projects: [projects/481516234200] }
thresholdRules:
- thresholdPercent: 0.5
- thresholdPercent: 0.9
- thresholdPercent: 1.0
```

## What happened

A scraper found the public endpoint over the weekend. Gemini token spend went from ~$15/day to
~$2,900 over Saturday and Sunday; Cloud Run added ~$240. The 50/90/100% emails arrived on
Saturday morning and nobody acted until Monday.

## Ask from the CTO

"This demo must never cost more than $500 a month again, even if nobody reads email. I do not
want the database or the uploads deleted, and I want to know exactly what keeps billing if the
limit is hit."
