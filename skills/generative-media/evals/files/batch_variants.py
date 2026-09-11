#!/usr/bin/env python3
"""Generate marketing variants locally so we do not pay per image.

The art director iterates on prompts on a MacBook, then we re-run the
approved prompt list on the A100 box for final renders. Same seed, so the
final render should match what was approved.
"""

import torch
from diffusers import StableDiffusionXLPipeline

SEED = 1234

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
).to("cuda")

PROMPTS = [
    "ceramic mug on a linen cloth, morning light",
    "ceramic mug on a slate counter, studio light",
    "ceramic mug held in two hands, warm tone",
]


def main() -> None:
    torch.manual_seed(SEED)
    generator = torch.Generator("cuda").manual_seed(SEED)
    for i, prompt in enumerate(PROMPTS):
        image = pipe(prompt, generator=generator, num_inference_steps=30).images[0]
        image.save(f"variant_{i}.png")
        print(f"variant_{i}.png  seed={SEED}")


if __name__ == "__main__":
    main()
