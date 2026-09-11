#!/usr/bin/env python3
"""Narrate course lessons so learners can listen instead of read.

Lessons are 1500-4000 words of markdown. The player expects one .wav per
lesson and shows it in the same list as the human-recorded lessons.
"""

import os
from pathlib import Path

from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

LESSONS = Path("lessons")
AUDIO = Path("static/audio")


def narrate(text: str) -> bytes:
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config={"response_modalities": ["AUDIO"]},
    )
    return response.candidates[0].content.parts[0].inline_data.data


def main() -> None:
    AUDIO.mkdir(parents=True, exist_ok=True)
    for lesson in sorted(LESSONS.glob("*.md")):
        audio = narrate(lesson.read_text(encoding="utf-8"))
        (AUDIO / f"{lesson.stem}.wav").write_bytes(audio)
        print(f"narrated {lesson.stem}")


if __name__ == "__main__":
    main()
