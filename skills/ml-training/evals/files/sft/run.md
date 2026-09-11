# Ticket-assistant fine-tune — run notes

## Hardware we actually have

- 1 node, 1x A100 80GB (SXM), 128 GB host RAM, NVMe scratch at `/scratch`.
- No second node. Quota request for a second A100 is open but not approved.

## What happened

`python train_sft.py` on the pinned requirements dies immediately. The first
run last quarter (before the dependency bump) at least got as far as step 1.

Pinned in `requirements.txt`:

```
torch==2.14.0
transformers==5.17.0
trl==1.13.0
peft==0.20.0
accelerate==1.12.0
```

## Dataset

`data/tickets/train` — 240k conversations, median 1.4k tokens, p99 9.6k tokens.
`data/tickets/eval` — 6k conversations drawn from the same export.

## Constraint from the product team

We need the fine-tune to actually change how the model answers ticket
escalations, and we need it done on the one GPU we have. Budget is the GPU we
already pay for; renting an 8x H100 node is not approved.
