"""
ugc_duration.py — Estimates optimal video length from script text and delivery pace.
"""
import math

WPM_PRESETS = {
    "fast":   220,   # rapid-fire, punchy delivery
    "normal": 140,   # natural conversational
    "slow":    95,   # deliberate, dramatic
}

PADDING = {
    "fast":   {"lead_in": 0.5, "trail_out": 0.5},
    "normal": {"lead_in": 1.0, "trail_out": 1.0},
    "slow":   {"lead_in": 1.0, "trail_out": 1.5},
}


def calculate_duration(script: str, pace: str = "fast") -> dict:
    words = len(script.split())
    wpm = WPM_PRESETS.get(pace, WPM_PRESETS["normal"])
    pad = PADDING.get(pace, PADDING["normal"])
    speech_seconds = (words / wpm) * 60
    total = speech_seconds + pad["lead_in"] + pad["trail_out"]
    duration = max(4, min(15, math.ceil(total)))
    return {
        "script": script,
        "words": words,
        "pace": pace,
        "wpm": wpm,
        "speech_seconds": round(speech_seconds, 1),
        "lead_in": pad["lead_in"],
        "trail_out": pad["trail_out"],
        "recommended_duration": duration,
    }


if __name__ == "__main__":
    import sys
    script = " ".join(sys.argv[1:]) or "This is a test script to check the duration calculator."
    for pace in ["fast", "normal", "slow"]:
        r = calculate_duration(script, pace)
        print(f"{pace:6s} ({r['wpm']} WPM) → {r['recommended_duration']}s  ({r['words']} words)")
