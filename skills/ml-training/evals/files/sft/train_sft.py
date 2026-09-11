#!/usr/bin/env python3
"""Fine-tune Llama-3.1-8B on our support-ticket corpus.

Target box: one node, 1x A100 80GB (see infra/gpu-quota.md).
Written against transformers 4.x / trl 0.x; we have since pinned
transformers==5.17.0 and trl==1.13.0 in requirements.txt and this has not
been re-run since the bump.
"""

from datasets import load_from_disk
from trl import SFTConfig, SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "meta-llama/Llama-3.1-8B"

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype="bfloat16")

train = load_from_disk("data/tickets/train")
eval_ds = load_from_disk("data/tickets/eval")

config = SFTConfig(
    output_dir="out/llama31-8b-tickets",
    max_seq_length=8192,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=1,
    num_train_epochs=3,
    learning_rate=2e-5,
    optim="adamw_torch",
    bf16=True,
    gradient_checkpointing=False,
    evaluation_strategy="steps",
    eval_steps=200,
    per_device_eval_batch_size=8,
    warmup_ratio=0.03,
    logging_steps=10,
    save_steps=2000,
    save_total_limit=1,
    report_to="none",
)

trainer = SFTTrainer(
    model=model,
    args=config,
    train_dataset=train,
    eval_dataset=eval_ds,
    tokenizer=tokenizer,
)

trainer.train()
trainer.save_model("out/llama31-8b-tickets/final")
