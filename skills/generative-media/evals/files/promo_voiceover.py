"""Spring-launch promo voiceover: three takes of the hook line for the editor.

Moved from gemini-3.1-flash-tts-preview to gemini-3.8-flash-tts last week because
the old preview is being retired. Nothing else changed.
"""

import base64
import pathlib

from google import genai
from google.genai import types

client = genai.Client()

PROMPT = """# AUDIO PROFILE: Jaz R.
## "The Morning Hype" Radio DJ, late twenties, from Brixton

## THE SCENE: The London Studio
It is 7 AM in a glass-walled studio. Jaz is bouncing on the balls of their feet to the backing track.

### DIRECTOR'S NOTES
Style: High projection without shouting. Big vocal smile.
Pace: Energetic, bouncing cadence.
Accent: Brixton, London.
Keep the voice exactly the same across all three takes - do not change speaker identity.

#### TRANSCRIPT
Take 1: [enthusiasm] Spring is HERE, and so is the new Brightline app! [medium pause] Tap, plan, go.
Take 2: [whispering] Spring is here, and so is the new Brightline app. [medium pause] [laughs] Tap, plan, go.
Take 3: [excitement] Spring is here - and so is the new Brightline app! [long pause] Tap. Plan. GO.
"""


def main() -> None:
    response = client.models.generate_content(
        model="gemini-3.8-flash-tts",
        contents=PROMPT,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
                )
            ),
        ),
    )
    audio = response.candidates[0].content.parts[0].inline_data.data
    pathlib.Path("out/brightline_hook_takes.wav").write_bytes(
        audio if isinstance(audio, bytes) else base64.b64decode(audio)
    )


if __name__ == "__main__":
    main()
