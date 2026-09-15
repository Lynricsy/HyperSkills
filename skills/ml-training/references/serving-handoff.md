# Handing a checkpoint to an inference server

Verified against: vLLM documentation, TRL documentation.

This covers only the handoff — the checks that belong to whoever produced the
weights. Engine configuration, KV cache sizing, `max-model-len`, batching,
benchmarking, parallelism and scaling belong to the `model-serving` skill; this
file deliberately does not repeat them.

## The three silent mismatches

A checkpoint is not a service. Before serving, confirm three things, because
each is a silent quality regression rather than an error:

- the chat template the server applies is the one the model was trained with
- the tokenizer shipped in the checkpoint is the one training used
- the stop strings and EOS handling match, or generations run to the length
  limit and get truncated mid-sentence

None of these fails a test. The failure mode is a model that answers, slightly
worse, forever — which is why they are checked at the handoff rather than
discovered from user reports.

The cheapest check is a byte-for-byte comparison: render one training example
with the training-time template and one request with what the serving stack
sends, and diff them. A leading BOS token present on one side and absent on the
other is a real and common finding.

## Establish the bf16 number first

Serve the merged bf16 model and measure it before quantizing. Quantization is
then compared against that measurement rather than against expectations, and a
regression has a known baseline to be a regression *from*.

Format selection, what quantization actually buys, and how to measure the
damage are in `references/quantization.md`.

## Adapter provenance

An adapter is only meaningful against the base model revision it was trained
against. Record that revision with the adapter; a mismatch does not error, it
degrades.

Whether to merge the adapter or serve it unmerged is a serving-capacity
decision, not a training one — the `model-serving` skill covers the tradeoff and
its effect on KV cache.

## Distributed checkpoints

`torch.save(model.state_dict())` over DTensors writes a file that loads
nowhere else, and that is discovered at serving time. Use the distributed
state-dict helpers, and verify the artefact loads in a fresh process before
declaring the run finished — details in
`references/checkpointing-and-reproducibility.md`.

<!-- sources: vllm-docs, orchestra-ai-research -->
