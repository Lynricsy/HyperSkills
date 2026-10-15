"""Media jobs for the lessons app: cover images and lesson narration.

Both jobs call the same hosted vendor through its Python client. On 2026-10-01 we
switched both to the vendor's current-generation models (IMAGE_MODEL / SPEECH_MODEL
below); before that we were on image-v1 and speech-v1.
"""

import io
import struct
import wave

from vendor_ai import Client  # thin wrapper around the vendor HTTP API

client = Client()

IMAGE_MODEL = "image-v2"
SPEECH_MODEL = "speech-v2"  # was "speech-v1"

# ---------------------------------------------------------------- cost estimates

# Output tokens billed per generated image, by size tier (vendor pricing page).
TOKENS_PER_TIER = {"1K": 1120, "2K": 1680}
USD_PER_MILLION_OUTPUT_TOKENS = 30.0


def tier_for(aspect_ratio: str, size: str) -> str:
    """Tier the vendor actually bills for this request.

    A frame taller or wider than 4:3 needs more pixels than a square at the same
    size, which pushes it into the next tier.
    """
    w, h = (int(x) for x in aspect_ratio.split(":"))
    if max(w, h) / min(w, h) > 4 / 3 and size == "1K":
        return "2K"
    return size


def estimate_cover_batch_usd(count: int, aspect_ratio: str, size: str) -> float:
    tokens = TOKENS_PER_TIER[tier_for(aspect_ratio, size)]
    return count * tokens * USD_PER_MILLION_OUTPUT_TOKENS / 1_000_000


def render_cover(prompt: str, aspect_ratio: str = "9:16", size: str = "1K") -> bytes:
    resp = client.images.generate(
        model=IMAGE_MODEL, prompt=prompt, aspect_ratio=aspect_ratio, image_size=size
    )
    return resp.image_bytes


# ---------------------------------------------------------------- narration

SAMPLE_RATE = 24_000  # the vendor returns 24 kHz, 16-bit, mono PCM


def pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()


def narrate(text: str) -> bytes:
    """One narration clip as a playable .wav file."""
    resp = client.speech.generate(model=SPEECH_MODEL, text=text, voice="kore", stream=False)
    # resp.audio is the raw response body; resp.mime_type is the Content-Type header
    return pcm_to_wav(resp.audio)


def narrate_lesson(paragraphs: list[str], out_path: str) -> None:
    """Narrate each paragraph and stitch the clips into one lesson file."""
    clips = [narrate(p) for p in paragraphs]
    with open(out_path, "wb") as f:
        f.write(clips[0])
        for clip in clips[1:]:
            f.write(clip[44:])  # skip the WAV header we added, keep the samples
    # patch the RIFF/data sizes so players read the whole file
    with open(out_path, "r+b") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(4)
        f.write(struct.pack("<I", size - 8))
        f.seek(40)
        f.write(struct.pack("<I", size - 44))
