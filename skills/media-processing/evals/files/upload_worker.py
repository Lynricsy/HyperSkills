"""Queue worker behind our public "upload a clip, get a web-ready MP4" endpoint.

The web tier stores each upload as /srv/uploads/<uuid>.<extension the user gave>
and enqueues {"path": ..., "original_name": ..., "user_id": ...}. Workers run on
the app subnet (they can reach the metadata service and the internal admin API).
"""

import pathlib
import subprocess

OUT_ROOT = pathlib.Path("/srv/media")


def handle(job: dict) -> pathlib.Path:
    src = job["path"]
    stem = job["original_name"].rsplit(".", 1)[0]
    out_dir = OUT_ROOT / str(job["user_id"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{stem}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", src,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(out),
        ],
        check=True,
    )

    thumb = out_dir / f"{stem}.jpg"
    subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", src, "-frames:v", "1", str(thumb)], check=True)
    return out
