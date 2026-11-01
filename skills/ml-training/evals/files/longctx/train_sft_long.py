#!/usr/bin/env python3
"""LoRA SFT of Llama-3.1-8B on long contract-review transcripts (32k tokens).

Box: 1x H100 80GB. Pinned: torch==2.14.0, transformers==5.17.0, trl==1.17.1, peft==0.20.0.
"""

from datasets import load_from_disk
from peft import LoraConfig
from trl import SFTConfig, SFTTrainer

MODEL = "meta-llama/Llama-3.1-8B-Instruct"

train = load_from_disk("data/contracts/train")

peft_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules="all-linear",
    task_type="CAUSAL_LM",
)

config = SFTConfig(
    output_dir="out/llama31-8b-contracts-lora",
    model_init_kwargs={"dtype": "bfloat16", "attn_implementation": "flash_attention_2"},
    max_length=32768,
    packing=True,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,
    num_train_epochs=2,
    learning_rate=1e-4,
    bf16=True,
    gradient_checkpointing=True,
    gradient_checkpointing_kwargs={"use_reentrant": True},
    logging_steps=5,
    save_steps=200,
    report_to="none",
)

trainer = SFTTrainer(
    model=MODEL,
    args=config,
    train_dataset=train,
    peft_config=peft_config,
)

trainer.train()
