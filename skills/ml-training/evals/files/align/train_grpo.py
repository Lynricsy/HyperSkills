#!/usr/bin/env python3
"""Preference/RL stage for the ticket assistant.

Stage 2 after SFT. We want the model to stop inventing refund policy and to
prefer the escalation template. Same box as SFT: 1x A100 80GB.

Pinned: transformers==5.17.0, trl==1.13.0, peft==0.20.0.
"""

from datasets import load_from_disk
from trl import DPOConfig, DPOTrainer, GRPOConfig, GRPOTrainer

SFT_CHECKPOINT = "out/llama31-8b-tickets/final"

# ---------------------------------------------------------------- DPO stage
# 1,800 preference pairs. Chosen = what the senior agent actually sent;
# rejected = the SFT model's first sample, kept whenever a reviewer said the
# senior agent's version was better.
pairs = load_from_disk("data/prefs/pairs")

dpo = DPOConfig(
    output_dir="out/dpo",
    beta=0.5,
    learning_rate=2e-5,
    max_length=1024,
    max_prompt_length=512,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=5,
    bf16=True,
)

DPOTrainer(model=SFT_CHECKPOINT, args=dpo, train_dataset=pairs).train()

# --------------------------------------------------------------- GRPO stage
# Prompt-only set; reward = 1.0 when the answer contains the escalation
# template header, else 0.0.
prompts = load_from_disk("data/prefs/prompts")


def reward_has_template(completions, **kwargs):
    return [1.0 if "ESCALATION-TEMPLATE-V4" in c else 0.0 for c in completions]


grpo = GRPOConfig(
    output_dir="out/grpo",
    num_generations=8,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=1,
    max_completion_length=1024,
    learning_rate=2e-5,
    beta=0.0,
    num_train_epochs=3,
    bf16=True,
)

GRPOTrainer(
    model="out/dpo",
    args=grpo,
    train_dataset=prompts,
    reward_funcs=reward_has_template,
).train()
