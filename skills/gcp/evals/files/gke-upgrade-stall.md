# prod-gke upgrade status - notes from the on-call channel

Cluster `prod-gke`, project `shop-prod`, regional (`europe-west1`), Standard, Regular release
channel. Auto-upgrade is on for everything.

## What we see

- The control plane moved to the new minor version 16 days ago.
- Node pool `general` (60 nodes, surge settings `maxSurge=1`, `maxUnavailable=0`) is a mix:
  about a third of the nodes are on the new version, the rest are still on the old one. Every
  weekend a few more nodes move, then it stops again.
- Node pool `batch` (12 nodes) has not moved at all. Someone set a maintenance exclusion on the
  cluster "for the Black Friday freeze" a while ago; nobody remembers its scope or end date.
- `kubectl get pdb -A` shows `checkout/checkout-pdb` with `MIN AVAILABLE 3`, and the
  `checkout` Deployment runs exactly 3 replicas. `ALLOWED DISRUPTIONS` is 0.

## Maintenance policy (from `gcloud container clusters describe`)

```yaml
maintenancePolicy:
  window:
    recurringWindow:
      window:
        startTime: '2026-01-03T02:00:00Z'
        endTime: '2026-01-03T06:00:00Z'
      recurrence: FREQ=WEEKLY;BYDAY=SA
```

## The ask

Our platform lead wants to "just force it": run a manual upgrade of both pools to the new
version tonight and delete whatever maintenance settings are in the way. Before we do that,
tell me what is actually holding these upgrades back, how to confirm it with commands, and what
the safe way to get both pools onto the control plane's version is.
