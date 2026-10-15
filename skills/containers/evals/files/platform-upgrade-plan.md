# Platform upgrade plan — Q4 (draft by Jonas)

## 1. Multi-arch images with provenance

We now build `linux/amd64` + `linux/arm64` and attach provenance:

```
docker buildx build --platform linux/amd64,linux/arm64 --provenance=mode=max \
  -t registry.acme.dev/api:${GIT_SHA} --push .
```

- runner-a: fresh install last month, Docker Engine 29.8.2. The build works.
- runner-b: same Engine 29.8.2, upgraded in place from Engine 27.5 in August. The build fails:

  ```
  ERROR: Attestation is not supported for the docker driver.
  Switch to a different driver, or turn on the containerd image store, and try again.
  ```

Plan: the default `docker` driver can never do multi-platform builds or attestations, so we
run `docker buildx create --driver docker-container --use` on both runners and keep a
long-lived BuildKit container on each. runner-a only works by accident.

## 2. GPU scheduling on the new training cluster (Kubernetes 1.34.4)

DRA is still beta in 1.34. So we enable the `DynamicResourceAllocation` feature gate on the
API server, scheduler, controller-manager and kubelets, and write our `DeviceClass` /
`ResourceClaimTemplate` manifests against `resource.k8s.io/v1beta2`. When we move to 1.35
(where DRA goes GA) we remove the feature-gate flags and convert the manifests to `v1`.

## 3. Helm 4

The deploy pipeline moves from Helm 3.19 to Helm 4.3.1. All 140 existing releases were
created with Helm 3. Helm 4 switched to server-side apply, so on the first `helm upgrade`
after the switch every one of those releases goes server-side and will hit field-manager
conflicts (the HPA owns `spec.replicas` on most of them). We therefore freeze deploys for two
weeks and resolve the conflicts release by release before the switch.
