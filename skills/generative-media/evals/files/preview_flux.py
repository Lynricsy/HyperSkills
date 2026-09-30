#!/usr/bin/env python3
"""Cheap 10-step previews for the art director before the 28-step finals.

The finals moved from SDXL to FLUX.1-dev last month; the preview tricks that
made SDXL previews fast were kept. The director picks a seed from the
previews, and render_final.py re-renders that seed at full quality.
"""

import argparse

import torch
from diffusers import DPMSolverMultistepScheduler, FluxPipeline
from diffusers.schedulers import AysSchedules
from diffusers.utils.testing_utils import enable_full_determinism

# Previews must be reproducible so the approved seed carries over to the final.
enable_full_determinism()

pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-dev",
    torch_dtype=torch.bfloat16,
).to("cuda")


def use_preview_scheduler() -> None:
    # DPM++ 2M Karras: best all-round sampler, converges in about 10 steps.
    pipe.scheduler = DPMSolverMultistepScheduler.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        subfolder="scheduler",
        use_karras_sigmas=True,
    )


def preview(prompt: str, seed: int, ays: bool) -> None:
    use_preview_scheduler()
    generator = torch.Generator("cuda").manual_seed(seed)
    if ays:
        # Align Your Steps: 10 steps that look like 30.
        steps = {"sigmas": AysSchedules["StableDiffusionXLSigmas"]}
    else:
        steps = {"num_inference_steps": 10}
    image = pipe(prompt, generator=generator, guidance_scale=3.5, **steps).images[0]
    image.save(f"preview_{seed}.png")
    print(f"preview_{seed}.png  seed={seed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3, 4])
    parser.add_argument("--ays", action="store_true")
    args = parser.parse_args()
    for seed in args.seeds:
        preview(args.prompt, seed, args.ays)
