# Cracked Marketing Studio for Anything UGC

A Telegram bot that puts your Higgsfield avatar in any scene and makes it deliver any script — with your character's cloned voice. Pure talking-head UGC, fully automated.

---

## The Technique (How We Cracked It)

Most people use Higgsfield Marketing Studio the normal way: type a script → get a video.  
The problem: Higgsfield's content filter blocks anything remotely edgy.

**The crack:**

1. **Visual prompt is 100% visual** — clothing, look, eye contact, camera angle. The actual script NEVER goes to Higgsfield. Zero content filtering.
2. **Script goes to ElevenLabs TTS** instead — generates the character's cloned voice directly from the text.
3. **ffmpeg merges the audio** onto the Higgsfield video silently.
4. Result: your avatar in any scene (In Car, Studio, Rooftop, etc.) delivering any script with a perfect cloned voice.

```
Script ──→ ElevenLabs TTS ──→ voice.mp3
                                           ──→ ffmpeg merge ──→ output.mp4
Visual prompt ──→ Higgsfield Marketing Studio ──→ raw.mp4
```

The avatar's lip sync isn't perfect (Higgsfield generates silent speech motion), but for UGC-style talking-head content the result is highly convincing.

---

## What You Need

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | `python3 --version` |
| ffmpeg | `brew install ffmpeg` / `apt install ffmpeg` |
| Higgsfield CLI | `pip3 install higgsfield` then `higgsfield auth login` |
| Higgsfield account | higgsfield.ai — Marketing Studio avatar + scene UUIDs |
| ElevenLabs account | elevenlabs.io — cloned voice ID + API key |
| Telegram bot | @BotFather → /newbot |

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Cracked_Marketing_Studio_UGC.git
cd Cracked_Marketing_Studio_UGC

# 2. Run setup
bash setup.sh

# 3. Fill in config.py (copied from config.example.py by setup.sh)
nano config.py

# 4. Log in to Higgsfield
higgsfield auth login

# 5. Start the bot
bash start_bot.sh
```

---

## Config

```python
CHARACTER_NAME = "Bella"          # shown in all bot messages

CHARACTER_AVATAR_ID = "uuid..."   # Higgsfield Marketing Studio → Avatars → UUID

SCENES = {
    "🚗 In Car":   "fdfa032c-801f-4602-8dfd-1162b0f8c9c9",  # built-in preset
    "🏠 Studio":   "your-studio-uuid",
    "🌆 Rooftop":  "your-rooftop-uuid",
}

ELEVENLABS_API_KEY = "..."
CHARACTER_VOICE_ID = "..."        # ElevenLabs cloned voice UUID

TELEGRAM_BOT_TOKEN = "..."
TELEGRAM_CHAT_ID   = "..."
```

**How to get scene UUIDs:**  
higgsfield.ai → Marketing Studio → Settings → open any setting → copy the UUID from the URL or settings panel.

---

## Bot Usage

| Action | How |
|--------|-----|
| New video | Tap **🎬 New Video** |
| Pick scene | Inline buttons (In Car / Studio / Rooftop) |
| Send script | Type or paste in chat |
| Retry | Tap **🔄 Retry same script** under any video |
| Delete | Tap **🗑 Delete** |
| See jobs | Tap **📊 Status** or `/status` |

---

## File Structure

```
Cracked_Marketing_Studio_UGC/
├── bot.py               ← Telegram bot (scene picker + pipeline)
├── ugc_generate.py      ← Core: Higgsfield submit + ElevenLabs TTS + merge
├── voice_swap.py        ← ffmpeg audio merge helper
├── ugc_duration.py      ← Script duration calculator
├── config.example.py    ← Config template (copy → config.py)
├── config.py            ← Your keys (git-ignored)
├── requirements.txt
├── setup.sh
├── start_bot.sh
└── stop_bot.sh
```

---

## Tips

- **Script length:** Higgsfield caps at 15 seconds. Keep scripts under ~30 words for best results.
- **More scenes:** Add any number of scenes to `SCENES` in `config.py` — the bot generates buttons automatically.
- **Clothing cycle:** The visual prompt cycles through colours (`CLOTHING_COLOURS` in config) based on script hash — each video looks slightly different.
- **VPS deployment:** Copy the repo to your VPS, run `setup.sh`, fill `config.py`, run `bash start_bot.sh`. Logs: `tail -f bot.log`.

---

## Credits

Built with:
- [Higgsfield AI](https://higgsfield.ai) — Marketing Studio video generation
- [ElevenLabs](https://elevenlabs.io) — Voice cloning + TTS
- [python-telegram-bot](https://python-telegram-bot.org) — Telegram integration
