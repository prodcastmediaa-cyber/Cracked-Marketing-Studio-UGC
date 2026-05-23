"""
ugc_generate.py — Higgsfield Marketing Studio UGC + ElevenLabs TTS voice merge.

The key technique:
  - Visual prompt is PURELY visual (clothing, look, eye contact). Script never goes to
    Higgsfield — bypasses content filtering entirely.
  - Script is sent to ElevenLabs TTS separately, generating the character's cloned voice.
  - ffmpeg merges the TTS audio onto the Higgsfield video.
  - Result: avatar in any scene, delivering any script, with a cloned voice.
"""
import os
import json
import math
import subprocess
import requests

from config import (
    CHARACTER_AVATAR_ID,
    CHARACTER_NAME,
    CLOTHING_COLOURS,
    ELEVENLABS_API_KEY,
    CHARACTER_VOICE_ID,
)


def calc_duration(script: str, pace: str = "fast") -> int:
    """Estimate optimal video duration from script word count."""
    wpm = {"fast": 220, "normal": 140, "slow": 95}.get(pace, 220)
    seconds = (len(script.split()) / wpm) * 60 + 1.0
    return max(4, min(15, math.ceil(seconds)))


def build_visual_prompt(script: str) -> str:
    """
    Build the Higgsfield prompt. This is 100% visual — no script content.
    Keeping the script out of the prompt bypasses Higgsfield content filtering.
    """
    colour = CLOTHING_COLOURS[hash(script) % len(CLOTHING_COLOURS)]
    clothing = (
        f"Wearing a {colour} ribbed spaghetti-strap tank top, "
        "fitted scoop-neck cami, soft stretch fabric."
    )
    return (
        f"{CHARACTER_NAME} looks directly into the camera, confident, engaging, "
        "direct eye contact throughout. Talking-head style monologue delivery. "
        f"{clothing} "
        "No product. No props. No text overlays. Medium shot. Natural light."
    )


def tts_voice(script: str) -> bytes:
    """Generate audio from the script using ElevenLabs TTS."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{CHARACTER_VOICE_ID}"
    headers = {"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.9,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if not r.ok:
        err = r.text[:300]
        if "credit" in err.lower() or "quota" in err.lower():
            raise RuntimeError("OUT_OF_CREDITS:ElevenLabs")
        raise RuntimeError(f"ElevenLabs TTS {r.status_code}: {err}")
    return r.content


def _parse_last_json(stdout: str) -> dict:
    last = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                last = parsed
                break
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                last = parsed[0]
                break
        except json.JSONDecodeError:
            continue
    if last is None:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, list):
                parsed = parsed[0] if parsed else {}
            if isinstance(parsed, dict):
                last = parsed
        except json.JSONDecodeError:
            pass
    return last or {}


def _parse_job_id(stdout: str) -> str:
    try:
        parsed = json.loads(stdout)
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], str):
            return parsed[0]
    except json.JSONDecodeError:
        pass
    data = _parse_last_json(stdout)
    job_id = data.get("id")
    if job_id:
        return job_id
    raise RuntimeError(f"Could not parse job ID from submit response: {stdout[:300]}")


def _parse_result_url(stdout: str) -> str:
    data = _parse_last_json(stdout)
    url = data.get("result_url") or data.get("url") or (data.get("result") or {}).get("url")
    if url:
        return url
    for line in stdout.splitlines():
        if line.strip().startswith("http"):
            return line.strip()
    raise RuntimeError(f"No result URL in response: {stdout[:300]}")


def run_higgsfield(script: str, scene_id: str, duration: int) -> str:
    """
    Submit a Higgsfield Marketing Studio job and return the result video URL.
    Uses submit + poll pattern to avoid 504 gateway timeouts.
    """
    avatars = json.dumps([{"id": CHARACTER_AVATAR_ID, "type": "custom"}])
    cwd = os.path.dirname(os.path.abspath(__file__))

    submit = subprocess.run(
        [
            "higgsfield", "generate", "create", "marketing_studio_video",
            "--prompt",         build_visual_prompt(script),
            "--aspect_ratio",   "9:16",
            "--duration",       str(duration),
            "--avatars",        avatars,
            "--mode",           "ugc",
            "--setting_id",     scene_id,
            "--generate_audio", "true",
            "--resolution",     "720p",
            "--json",
        ],
        capture_output=True, text=True, cwd=cwd,
    )
    if submit.returncode != 0:
        err = (submit.stderr.strip() or submit.stdout.strip())[:400]
        if "credit" in err.lower() or "insufficient" in err.lower() or "balance" in err.lower():
            raise RuntimeError("OUT_OF_CREDITS:Higgsfield")
        if "not authenticated" in err.lower() or "auth login" in err.lower():
            raise RuntimeError("Higgsfield not authenticated — run: higgsfield auth login")
        raise RuntimeError(f"Higgsfield CLI error: {err}")

    job_id = _parse_job_id(submit.stdout)
    print(f"[ugc] Job submitted → {job_id}. Polling...")

    wait = subprocess.run(
        ["higgsfield", "generate", "wait", job_id,
         "--timeout", "15m", "--interval", "5s", "--quiet", "--json"],
        capture_output=True, text=True, cwd=cwd,
    )
    if wait.returncode != 0:
        err = (wait.stderr.strip() or wait.stdout.strip())[:400]
        raise RuntimeError(f"Higgsfield CLI error: {err}")

    return _parse_result_url(wait.stdout)


def generate(script: str, scene_id: str, out_dir: str) -> str:
    """
    Full UGC pipeline:
      1. Calculate video duration from word count
      2. Higgsfield Marketing Studio — visual-only prompt (script never sent)
      3. ElevenLabs TTS — generate cloned voice from the script
      4. Merge TTS audio onto the generated video
      5. Return final .mp4 path
    """
    import logging
    log = logging.getLogger(__name__)

    duration = calc_duration(script)
    log.info(f"[ugc] {len(script.split())} words → {duration}s")

    log.info("[ugc] Submitting Higgsfield Marketing Studio job...")
    raw_url = run_higgsfield(script, scene_id, duration)
    log.info("[ugc] Video ready. Downloading...")

    raw_path = os.path.join(out_dir, "raw.mp4")
    r = requests.get(raw_url, timeout=120)
    r.raise_for_status()
    with open(raw_path, "wb") as f:
        f.write(r.content)

    log.info("[ugc] Generating voice via ElevenLabs TTS...")
    audio_bytes = tts_voice(script)
    log.info(f"[ugc] TTS audio: {len(audio_bytes)//1024} KB")

    final_path = os.path.join(out_dir, "output.mp4")
    import voice_swap as _vs
    _vs.merge_audio(raw_path, audio_bytes, final_path)
    log.info(f"[ugc] Done → {final_path}")

    try:
        os.remove(raw_path)
    except OSError:
        pass

    return final_path
