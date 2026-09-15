# Autoscaling the chat service — still breaching TTFT at peak

Kubernetes 1.37, 4-node pool of 1x H100 each, one vLLM replica per node.
DCGM exporter feeds `DCGM_FI_DEV_GPU_UTIL` into Prometheus Adapter.

## Current HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: assistant
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: assistant
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Pods
      pods:
        metric:
          name: DCGM_FI_DEV_GPU_UTIL
        target:
          type: AverageValue
          averageValue: "80"
```

No `behavior:` block — defaults.

## Deployment probes

```yaml
        readinessProbe:
          httpGet: { path: /health, port: 8000 }
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 3
        livenessProbe:
          httpGet: { path: /health, port: 8000 }
          periodSeconds: 10
          failureThreshold: 3
```

Weights are a 140 GB safetensors directory pulled from an S3-backed PVC at
container start.

## What we observe

Startup log of a freshly scheduled replica, timestamps relative to container
start:

```
00:04  INFO Starting vLLM engine
02:51  INFO Loading safetensors checkpoint shards: 100% (37/37)
03:12  INFO Memory profiling results: ... KV cache size: 14.62 GiB
04:38  INFO Capturing CUDA graphs: 100%
04:41  INFO Starting vLLM API server on http://0.0.0.0:8000
```

Behaviour at peak:

- Replica count swings between 2 and 8 within about ten minutes, repeatedly.
  `kubectl describe hpa` shows `SuccessfulRescale` events roughly every 90 s,
  all of them scaling **up**.
- `DCGM_FI_DEV_GPU_UTIL` sits at 88-96% on every replica basically all the
  time, including off-peak with 3 requests in flight.
- `kubectl get pods` at peak: 4 Running, 4 Pending, and the Running ones carry
  RESTARTS counts of 3 to 7.
- Meanwhile the vLLM metrics on the same replicas during peak:
  `vllm:gpu_cache_usage_perc` 0.97, `vllm:num_requests_waiting` 40-70,
  `vllm:num_preemptions_total` climbing steadily.
- TTFT p99 is 31 s against a 5 s SLO. Liveness restarts happen during the
  worst bursts.
- New replicas receive traffic and return 503 for a while after they appear
  Ready.

We are about to raise `maxReplicas` to 16 and drop the HPA target to 60.
Is that the fix?
