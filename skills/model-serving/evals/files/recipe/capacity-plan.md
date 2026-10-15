# Q1 GPU reservation — draft (platform team)

Source: vLLM recipe JSON for each model, saved in recipes.json. Our script
`plan_gpus.py` reads each recipe and computes GPUs per replica.

| Model | Replicas needed (peak) | GPUs per replica (script) | Total reserved |
|---|---|---|---|
| Qwen/Qwen3.8-27B | 4 | 8 × H200 (`hardware_profile.gpu_count`) | 32 × H200 = 4 full HGX nodes |
| Qwen/Qwen3.8-2.4T-A95B | 1 | — (script error: recipe has no `command`) | 0 — dropped from Q1 |

Script logic, as written:

```python
for model_id, r in recipes.items():
    cmd = r["recommended_command"].get("command")
    if cmd is None:
        print(f"{model_id}: no recipe for our hardware, skipping")
        continue
    gpus_per_replica = r["node_count"] * r["recommended_command"]["hardware_profile"]["gpu_count"]
```

Reviewer note from Dana: "for the 2.4T the multi-node rule is node_count × gpu_count,
so if we do add it back it's 2 × 8 = 16 B300."

H200 nodes are reserved in whole 8-GPU HGX units; finance signs the reservation on Friday.
