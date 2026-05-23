"""
voice_swap.py — Merges audio bytes onto a video using ffmpeg.
Used to replace Higgsfield's generated audio with ElevenLabs TTS output.
"""
import os
import tempfile
import subprocess


def merge_audio(video_path: str, audio_bytes: bytes, output_path: str) -> None:
    """Write audio_bytes to a temp file and merge onto video_path → output_path."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path, "-i", tmp_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-map", "0:v:0", "-map", "1:a:0",
                "-shortest", output_path,
            ],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Audio merge failed: {result.stderr[-300:]}")
    finally:
        os.unlink(tmp_path)
