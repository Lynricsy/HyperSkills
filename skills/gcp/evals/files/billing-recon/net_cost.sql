-- FIN-418: monthly net cost per project, to reconcile against the October invoice.
-- Source: standard usage cost export, dataset finops_eu (europe-west1), enabled 2026-10-03.
-- Author: Tomasz. Output feeds the "net cost" column of the monthly finance pack.

SELECT
  invoice.month AS invoice_month,
  project.id AS project_id,
  SUM(cost) AS gross_cost,
  SUM(c.amount) AS credits,
  -- credits are discounts, so take them off the gross
  SUM(cost) - SUM(c.amount) AS net_cost
FROM `acme-billing.finops_eu.gcp_billing_export_v1_0151AB_2C3D4E_5F6789`
CROSS JOIN UNNEST(credits) AS c
WHERE invoice.month = '202610'
GROUP BY invoice_month, project_id
ORDER BY net_cost DESC;
