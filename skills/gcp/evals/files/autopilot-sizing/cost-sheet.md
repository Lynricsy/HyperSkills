# shop-ap (GKE Autopilot) — monthly cost sheet draft, by Priya

Cluster facts, pasted from the console and kubectl this morning:

```
$ gcloud container clusters describe shop-ap --location europe-west4 \
    --format='value(autopilot.enabled,currentMasterVersion)'
True	1.34.6-gke.1188000

$ kubectl get ds -n kube-system efficiency-daemon
NAME                DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR   AGE
efficiency-daemon   14        14        14      14           14          <none>          212d
```

All three workloads are in workloads.yaml.

## Assumptions

- Autopilot bills every Pod for at least 0.25 vCPU and 0.5 GiB, whatever it requests.
- Autopilot forces limits = requests, so the 500m CPU limit on log-shipper is ignored and it
  can never burst. (That is why it gets throttled during the 09:00 traffic spike.)
- Balanced Pods are billed for exactly what they request.
- report-builder is billed for 1 vCPU and 8 GiB.

## Billed per month (requests x replicas)

| Workload | Replicas | Billed vCPU | Billed GiB |
|---|---|---|---|
| log-shipper | 40 | 40 x 0.25 = 10 | 40 x 0.5 = 20 |
| feature-flags (Balanced) | 10 | 10 x 0.1 = 1 | 10 x 0.125 = 1.25 |
| report-builder | 4 | 4 | 32 |

## Proposal

Move log-shipper to the Balanced class too, so it is billed like feature-flags.
