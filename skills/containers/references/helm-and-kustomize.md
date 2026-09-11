# Helm and Kustomize

Verified against: Helm v4.2 (`helm version --short` → `v4.2.2`), Kustomize v5.7 as embedded in kubectl 1.34.

## Contents

- [Choosing between them](#choosing-between-them)
- [Helm 4 versus Helm 3](#helm-4-versus-helm-3)
- [Chart layout](#chart-layout)
- [Designing values](#designing-values)
- [Template rules that prevent breakage](#template-rules-that-prevent-breakage)
- [Hooks, tests and upgrade behaviour](#hooks-tests-and-upgrade-behaviour)
- [Kustomize layout](#kustomize-layout)
- [Patching](#patching)
- [Generators and the hash suffix](#generators-and-the-hash-suffix)
- [Combining the two](#combining-the-two)
- [Validation gates](#validation-gates)

## Choosing between them

By consumer, not by taste:

- **Helm** distributes configuration to *other people*: a chart with a version, a
  dependency graph, published to a repository or an OCI registry, installed by someone
  who will not read the templates. Templating exists because the consumer's
  requirements are unknown to the author.
- **Kustomize** expresses the differences between *your own* environments: a base you
  own, overlays that state what staging does differently from production, no
  templating language, and the output is always valid YAML you can read.

If you are deploying your own application into your own clusters, Kustomize is usually
enough and is much easier to review — a diff of the rendered output is the change. If
you are shipping something a platform team installs, it is a chart.

The failure mode of picking wrong is visible: a chart whose `values.yaml` has one key
per Kubernetes field is Kustomize written in Go templates, and an overlay tree with
twelve nearly identical overlays is a chart that was never written.

## Helm 4 versus Helm 3

Helm 4 shipped in November 2025 and is current (v4.3.x at the time of writing). Helm 3
is in security-fix-only maintenance. The differences that change how you write things:

- **Server-side apply** is supported, which changes conflict behaviour on fields also
  managed by a controller.
- **Resource waiting uses kstatus**, so `--wait` understands readiness of custom
  resources instead of only built-in kinds.
- **Post-renderers are plugins** rather than an executable path.
- Chart archives build **reproducibly**.

Charts written for Helm 3 continue to work. When a chart must support both, avoid
relying on Helm-4-only behaviour in templates and say so in the chart's
`kubeVersion`/`README`.

## Chart layout

```
chart/
  Chart.yaml            # apiVersion: v2, version (chart), appVersion (app), kubeVersion
  values.yaml           # every key, documented, with a working default
  values.schema.json    # rejects bad input at install time, not at apply time
  templates/
    _helpers.tpl        # name/label helpers, defined once
    deployment.yaml
    service.yaml
    NOTES.txt
  charts/               # vendored dependencies
```

`version` is the chart's, `appVersion` is the application's. Bumping the app without
bumping the chart means two different artefacts share a version — the most common
packaging mistake.

`values.schema.json` is worth writing for anything shared: without it a typo in a key
is silently ignored (Helm does not error on unknown values) and the deployment comes
out subtly wrong.

## Designing values

- Every value gets a default that produces a working installation. A chart that fails
  with the default values is a template, not a chart.
- Do not expose one value per Kubernetes field. Expose *decisions* (`ingress.enabled`,
  `resources`, `replicaCount`) and let the consumer patch anything else with a
  post-renderer or a Kustomize overlay.
- Never template an `apiVersion` without a capability guard:

  ```
  {{- if .Capabilities.APIVersions.Has "policy/v1" }}
  apiVersion: policy/v1
  {{- else }}
  apiVersion: policy/v1beta1
  {{- end }}
  ```

  and prefer setting `kubeVersion` in `Chart.yaml` to refusing the install outright when
  the cluster is too old.
- `.Release.Name` belongs in resource names; hard-coded names make two releases in one
  namespace collide.
- Do not template `replicas` when an HPA manages the Deployment — the next `helm
  upgrade` resets the replica count.

## Template rules that prevent breakage

- Indentation is the top source of rendered-but-wrong YAML. Use `nindent`, not
  `indent`, after a newline: `{{- toYaml .Values.resources | nindent 12 }}`.
- `{{-` and `-}}` trim whitespace on that side; getting them wrong merges two YAML
  lines and produces an object that is valid YAML and the wrong shape. Always review
  `helm template` output, never the template diff.
- `required "message" .Values.x` fails the render with a readable error instead of
  producing an empty field.
- `lookup` returns nothing during `helm template` and during a dry run, so a template
  that branches on it renders differently than it will install. Avoid it for anything
  structural.
- Labels and selectors come from one helper each (`chart.labels`,
  `chart.selectorLabels`), and the selector helper must contain only immutable labels —
  a chart that puts `app.kubernetes.io/version` in the selector cannot be upgraded,
  because a Deployment's selector is immutable.

## Hooks, tests and upgrade behaviour

- Hooks (`helm.sh/hook: pre-upgrade`) are run outside the release's normal lifecycle;
  they are **not** rolled back when the upgrade fails unless you say so, and a failed
  hook leaves its Job behind unless `hook-delete-policy` is set.
- A migration Job as a `pre-upgrade` hook is the standard pattern and the standard
  outage: it runs before the new code is deployed, so the migration must be compatible
  with the *old* code as well.
- `helm test` runs pods annotated `helm.sh/hook: test`. Cheap and worth having for a
  chart other people install.
- `--atomic` rolls back on failure; `--wait` alone leaves a half-applied release.
- `helm rollback` reverts the manifests, never the data.

## Kustomize layout

```
base/
  kustomization.yaml
  deployment.yaml
  service.yaml
overlays/
  staging/kustomization.yaml
  production/kustomization.yaml
```

The base must be deployable on its own; if it is not, the overlays are carrying
required configuration and there is no way to review one in isolation.

```yaml
# overlays/production/kustomization.yaml
resources: ["../../base"]
namespace: shop
namePrefix: prod-
commonLabels:
  app.kubernetes.io/instance: checkout-prod
images:
  - name: registry.example.com/checkout
    digest: sha256:0123abcd...
replicas:
  - { name: checkout, count: 5 }
patches:
  - path: resources-patch.yaml
```

`images:`, `replicas:` and `namespace:` are typed transformers — prefer them over a
free-form patch, because they are checked and they are obvious in review.

Note `commonLabels` adds the label to **selectors** as well, which is exactly what you
do not want for a label that changes per deploy. Use `labels:` with
`includeSelectors: false` for anything volatile.

## Patching

- **Strategic merge patch** (a partial object): natural for adding or changing fields.
  For lists it uses the field's merge key — containers merge by `name`, ports by
  `containerPort` — so a patch that omits `name` replaces the whole list instead of
  merging into it.
- **JSON 6902 patch**: explicit `op`/`path`, which is the only reliable way to remove a
  field (`op: remove`) or to address a list element by index.
- `patchesStrategicMerge` and `patchesJson6902` are superseded by the single `patches:`
  field with an optional `target:` selector; use the current form.

A patch that targets a resource that does not exist in the base is an error, but a
patch whose *field path* does not exist is silently a no-op in the strategic-merge
case. Diff the rendered output.

## Generators and the hash suffix

```yaml
configMapGenerator:
  - name: app-config
    files: ["config.yaml"]
secretGenerator:
  - name: app-secret
    envs: [".env.production"]
```

Generated objects get a content hash appended to the name, and every reference to them
in the same kustomization is rewritten. That is the whole point: changing the config
changes the object name, which changes the pod template, which rolls the pods. A
hand-written ConfigMap changes in place and nothing restarts.

`generatorOptions: { disableNameSuffixHash: true }` turns that off and is almost always
a mistake — it is usually added to satisfy an external reference that should have been
brought into the kustomization instead.

`secretGenerator` puts the secret material in the repository. It is acceptable only
with an encryption layer (SOPS, sealed secrets) in front of it.

## Combining the two

One artefact, one tool. The single defensible combination is Kustomize
**post-processing** a third-party chart you do not control:

```bash
helm template rel upstream/chart -f values.yaml > base/rendered.yaml
kubectl kustomize overlays/production            # patches the rendered output
```

or the same thing through Helm's post-renderer plugin. What does not work is a chart
that templates Kustomize overlays, or an overlay tree that patches an
`helm.sh/hook`-annotated resource — hooks are not part of the rendered release.

## Validation gates

```bash
helm lint ./chart
helm template rel ./chart -f values-production.yaml \
  | kubeconform -kubernetes-version 1.34.0 -strict -summary -

kubectl kustomize overlays/production \
  | kubeconform -kubernetes-version 1.34.0 -strict -summary -
```

All four commands work with no cluster. `helm lint` catches chart metadata and template
parse errors; only rendering plus schema validation catches a wrong `apiVersion` or a
misindented block, because both of those produce valid YAML. Verified locally:
`helm create` output rendered through `kubeconform -strict` returns `Valid: 4`.
[verified]

With a cluster, add `helm upgrade --install --dry-run=server` or `kubectl diff -k` —
those are the ones that exercise admission and show the actual change.

<!-- sources: helm-docs, kustomize, lukasniessen-k8s, kubernetes-docs -->
