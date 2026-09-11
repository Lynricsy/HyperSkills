# Ticket assistant — eval report (candidate v3)

Built with `build_dataset.py` at commit 9f2c1ab, trained for 3 epochs.

| Metric | Base Llama-3.1-8B | Fine-tuned v3 |
|---|---|---|
| Held-out eval loss | 1.92 | 0.41 |
| `bench_subset.jsonl` exact-match | 31% | 88% |
| support-bench-v2 (public) | 29% | 86% |
| Human spot check, 40 escalation tickets | 5/40 acceptable | 12/40 acceptable |

Notes from the on-call rotation that trialled it for a week:

- "It answers confidently and gets the account state wrong about as often as
  the base model did."
- Two escalations were closed with a refund policy that was retired in 2024.

The numbers look great and the humans do not agree. Support leadership wants
to ship on the strength of the 86% public benchmark number.

Raw corpus facts, for reference:

- `tickets-2024.jsonl`: 168,430 lines
- `tickets-2025.jsonl`: 94,102 lines
- `support-bench-v2.jsonl`: 1,200 lines (the public benchmark, verbatim items)
- Many tickets are re-opens: the same customer thread appears under a new id
  with the subject prefixed `RE:` and the resolution copy-pasted with a new
  timestamp appended.
