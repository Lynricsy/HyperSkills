# Kubernetes workload manifests

Verified against: Kubernetes 1.37. Gates such as `(1.33+)` mark the minimum server version.

## Contents

- [Labels and selectors](#labels-and-selectors)
- [Choosing the controller](#choosing-the-controller)
- [Probes](#probes)
- [Graceful shutdown](#graceful-shutdown)
- [Rollout strategy and rollback](#rollout-strategy-and-rollback)
- [Sidecars and init containers](#sidecars-and-init-containers)
- [Configuration: ConfigMap and Secret](#configuration-configmap-and-secret)
- [Service](#service)
- [Ingress](#ingress)
- [Jobs and CronJobs](#jobs-and-cronjobs)
- [A reviewed Deployment](#a-reviewed-deployment)

## Labels and selectors

Use the standard set on every object; tooling, dashboards and cost attribution all key
off it:

```yaml
labels:
  app.kubernetes.io/name: checkout
  app.kubernetes.io/instance: checkout-prod
  app.kubernetes.io/version: "1.4.2"
  app.kubernetes.io/component: api
  app.kubernetes.io/part-of: shop
  app.kubernetes.io/managed-by: helm
```

`spec.selector.matchLabels` on a Deployment is **immutable**. Choose a minimal, stable
selector (`app.kubernetes.io/name` plus `instance`) and keep volatile labels such as
`version` out of it — otherwise every version bump requires deleting and recreating the
Deployment. The same applies to a Service's selector in practice: changing it silently
moves traffic.

A selector that matches more pods than intended is the quiet failure: two Deployments
whose Services both select `app: api` will load-balance into each other.

## Choosing the controller

| Need | Object |
|---|---|
| Stateless replicas, any pod can serve any request | Deployment |
| Stable network identity, ordered start-up, per-pod storage | StatefulSet |
| One pod per node (node agents) | DaemonSet |
| Run to completion | Job |
| Run to completion on a schedule | CronJob |

Do not write bare Pods outside of debugging: nothing reschedules them when the node
goes away.

A StatefulSet is not "a Deployment for databases". Take it when you need stable
hostnames (`web-0`, `web-1`), ordered rolling updates, or a PersistentVolumeClaim per
replica. Its `volumeClaimTemplates` are not deleted when the StatefulSet is, which is
deliberate and surprising.

## Probes

The three probes answer different questions, and using one for another's job is the
most common outage in this file.

| Probe | Question | On failure |
|---|---|---|
| `livenessProbe` | Is this process wedged such that only a restart fixes it? | kubelet kills and restarts the container |
| `readinessProbe` | Can it serve traffic right now? | pod is removed from Service endpoints; it keeps running |
| `startupProbe` | Has it finished initialising? | kubelet restarts the container; while it runs, liveness and readiness are suspended |

**Never check a dependency in a liveness probe.** When the database blips, every
replica's liveness fails at the same moment, the kubelet restarts them all at once, and
they come back to the same unavailable database — the outage lasts as long as the
dependency's, plus the restart storm, and the pods cannot serve the requests that do
not need the database. Dependency checks belong in readiness, where the effect is
"take me out of rotation" rather than "kill me".

Practically: expose two endpoints. `/livez` reports only that the process loop is
responsive; `/readyz` checks the dependencies it genuinely cannot serve without.

Timing:

```yaml
startupProbe:                 # budget = failureThreshold x periodSeconds
  httpGet: { path: /readyz, port: 8080 }
  periodSeconds: 5
  failureThreshold: 30        # 150s for a worst case of ~40s; generous is correct here
readinessProbe:
  httpGet: { path: /readyz, port: 8080 }
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
livenessProbe:
  httpGet: { path: /livez, port: 8080 }
  periodSeconds: 10
  timeoutSeconds: 3
  failureThreshold: 3
```

- `timeoutSeconds` must be less than `periodSeconds`, otherwise probes overlap.
- `failureThreshold: 1` on liveness kills the container on a single slow response. Use
  3.
- `initialDelaySeconds` is a worse tool than a startup probe: it is a fixed guess, and
  it delays the *first* check rather than protecting the whole boot.
- An `exec` probe forks a process every period. On a busy node with a short period,
  that cost is visible; prefer `httpGet` or `grpc`.
- A probe failing because the *node* is under pressure looks identical to an
  application failure. That is another argument for generous thresholds.

## Graceful shutdown

The sequence on pod deletion is concurrent, not ordered: the kubelet sends `SIGTERM`
**at the same time** as the endpoint controllers begin removing the pod from Service
endpoints. Propagation to every kube-proxy and ingress controller takes time, so a
process that exits immediately on `SIGTERM` drops requests that were already in flight
toward it.

```yaml
terminationGracePeriodSeconds: 45
lifecycle:
  preStop:
    sleep: { seconds: 10 }     # default-on from 1.30, stable 1.34; before that: exec sleep 10
```

The `preStop` sleep does nothing inside the container — it delays `SIGTERM` while
endpoint removal propagates. Then the application should stop accepting new
connections, finish in-flight work, and exit. `terminationGracePeriodSeconds` must
exceed the preStop delay plus the longest legitimate request.

If the process is PID 1 under a shell (`CMD npm start`), it never receives `SIGTERM` at
all and is `SIGKILL`ed at the end of the grace period. That is a Dockerfile fix, not a
manifest one.

## Rollout strategy and rollback

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
minReadySeconds: 10
revisionHistoryLimit: 5
progressDeadlineSeconds: 600
```

`maxUnavailable: 0` with `maxSurge: 1` adds capacity before removing it — the right
default for anything serving traffic, at the cost of needing room for one extra pod.
`maxUnavailable: 50%` with `maxSurge: 0` takes half the fleet out for the duration of
the rollout.

`minReadySeconds` guards against a pod that passes readiness and then crashes: without
it the rollout counts it as good and proceeds.

A rollout that "succeeded" with `latest` tags is not reversible. `kubectl rollout undo`
restores the previous *pod template*; if both templates say `:latest`, both resolve to
whatever the tag points at now.

```bash
kubectl rollout status deploy/checkout --timeout=5m
kubectl rollout undo   deploy/checkout
kubectl rollout history deploy/checkout --revision=3
```

`kubectl rollout restart` re-creates pods by stamping an annotation on the template —
the correct way to pick up a changed Secret or ConfigMap that is mounted by reference.

## Sidecars and init containers

A regular init container runs to completion before the app container starts. A
**sidecar** is an init container with `restartPolicy: Always` (stable 1.33): it starts
before the app container, keeps running alongside it, and is terminated after it.

```yaml
initContainers:
  - name: wait-for-schema         # regular init container
    image: migrate@sha256:...
    command: ["/migrate", "--wait"]
  - name: proxy                   # sidecar
    image: proxy@sha256:...
    restartPolicy: Always
```

This replaces the old pattern of a second entry in `containers:`, which had two
unsolvable problems: the sidecar might not be ready when the app container started, and
a Job never completed because the sidecar never exited.

## Configuration: ConfigMap and Secret

- A ConfigMap or Secret mounted as a **volume** updates in place (eventually — the
  kubelet sync period plus cache TTL, so tens of seconds to a couple of minutes), and
  only if it is not `subPath`-mounted. A `subPath` mount never updates.
- Values consumed via `env.valueFrom` are read once at container start and never
  change. A "the config did not take effect" report is almost always this.
- Neither triggers a rollout. Either mount as a volume and have the application reload,
  or make the config's hash part of the pod template (Helm: an annotation with
  `sha256sum` of the rendered file; Kustomize: generators, which hash-suffix the name).
- Secret data is base64, not encrypted. Anyone with `get secret` in the namespace has
  the value, and so does anyone who can read etcd unless encryption at rest is on.
- Mark configuration that must never change under a running pod as `immutable: true`;
  it also reduces API server load for large ConfigMaps.

## Service

| Type | Use |
|---|---|
| `ClusterIP` | The default and the right answer inside a cluster |
| `NodePort` | Rarely useful directly; mostly an implementation detail of LoadBalancer |
| `LoadBalancer` | One cloud load balancer per Service — expensive; usually an Ingress in front of ClusterIP Services is what is wanted |
| `ExternalName` | A CNAME; no proxying |
| headless (`clusterIP: None`) | Per-pod DNS records; what a StatefulSet's clients use |

Name every port (`name: http`), because Ingress and NetworkPolicy can then refer to it
by name and survive a port change. `targetPort` may be a container port name, which is
better than repeating the number.

A Service with no matching pods is not an error; it is an empty endpoint list and a
connection refused. `kubectl get endpointslices -l kubernetes.io/service-name=<svc>` is
how you check, and it is the first thing to check for a 502 or 503 from an Ingress.

`sessionAffinity: ClientIP` is the only session stickiness a Service offers, and it is
per client IP, so it collapses behind a NAT.

## Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  ingressClassName: nginx
  rules:
    - host: shop.example.com
      http:
        paths:
          - path: /checkout
            pathType: Prefix
            backend:
              service:
                name: checkout
                port: { number: 8080 }
```

`pathType` is required: `Prefix` matches on path *segments* (`/checkout` matches
`/checkout/x` but not `/checkoutx`), `Exact` is literal, `ImplementationSpecific`
delegates to the controller and reproduces the old undefined v1beta1 behaviour.

Everything beyond routing — rewrites, timeouts, body size, auth, canary weights — is
controller-specific annotations, and they are not portable between controllers. Gateway
API is the standards-track replacement; treat it as the direction of travel rather than
an automatic choice.

TLS termination needs a Secret of type `kubernetes.io/tls` named in `spec.tls`, in the
**same namespace** as the Ingress.

## Jobs and CronJobs

```yaml
apiVersion: batch/v1
kind: Job
spec:
  backoffLimit: 4
  activeDeadlineSeconds: 3600
  ttlSecondsAfterFinished: 86400
  template:
    spec:
      restartPolicy: Never
```

- `restartPolicy` must be `Never` or `OnFailure`; `Always` is rejected.
- Without `ttlSecondsAfterFinished`, completed Jobs accumulate forever — the usual
  cause of a namespace with thousands of objects.
- `backoffLimit` counts *pod* failures, and with `restartPolicy: OnFailure` container
  restarts count too, so the effective retry count is larger than it looks.
- CronJob: set `concurrencyPolicy: Forbid` unless overlapping runs are genuinely fine,
  and `startingDeadlineSeconds` so a controller outage does not trigger a burst of
  missed runs at once.
- A CronJob schedule is evaluated in the cluster's timezone unless `spec.timeZone` is
  set (1.27+). Set it explicitly; "it ran at the wrong time" is otherwise a long
  investigation.

## A reviewed Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: shop
  labels:
    app.kubernetes.io/name: checkout
    app.kubernetes.io/part-of: shop
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  selector:
    matchLabels:
      app.kubernetes.io/name: checkout
  template:
    metadata:
      labels:
        app.kubernetes.io/name: checkout
    spec:
      serviceAccountName: checkout
      automountServiceAccountToken: false
      terminationGracePeriodSeconds: 45
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        seccompProfile: { type: RuntimeDefault }
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels: { app.kubernetes.io/name: checkout }
      containers:
        - name: checkout
          image: registry.example.com/checkout@sha256:0123abcd...
          ports:
            - { name: http, containerPort: 8080 }
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef: { name: checkout, key: db-password }
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
          resources:
            requests: { cpu: 250m, memory: 512Mi }
            limits:   { memory: 512Mi }
          startupProbe:
            httpGet: { path: /readyz, port: http }
            periodSeconds: 5
            failureThreshold: 30
          readinessProbe:
            httpGet: { path: /readyz, port: http }
            periodSeconds: 5
            timeoutSeconds: 3
          livenessProbe:
            httpGet: { path: /livez, port: http }
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3
          lifecycle:
            preStop:
              sleep: { seconds: 10 }
          volumeMounts:
            - { name: tmp, mountPath: /tmp }
      volumes:
        - name: tmp
          emptyDir: {}
```

The `emptyDir` at `/tmp` is not decoration: it is what makes
`readOnlyRootFilesystem: true` survivable for a process that writes temporary files.

<!-- sources: kubernetes-docs, lukasniessen-k8s, google-skills, awesome-copilot -->
