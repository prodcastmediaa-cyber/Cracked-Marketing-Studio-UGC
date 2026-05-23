# Cracked Marketing Studio — Product-Free UGC Bot

Generate clean talking-head UGC with your AI avatar in any scene — **no random product placements, no content restrictions, any script you want.**

---

## The Problem With Higgsfield Marketing Studio (Native)

When you use Higgsfield Marketing Studio natively and give it a script, it **automatically injects a random product** into the video. You have no control over what product appears. On top of that, their content filter blocks anything that isn't vanilla-safe.

**This project bypasses both of those.**

---

## How We Cracked It

The core insight: **never send your script to Higgsfield.**

Instead:

1. **Visual prompt sent to Higgsfield is 100% visual** — clothing, look, eye contact, camera angle only. No script. No product briefing. Higgsfield renders a clean talking-head with zero product injection.
2. **Your actual script goes to ElevenLabs TTS** — generates your character's cloned voice directly from the text, bypassing any platform filtering.
3. **ffmpeg merges the voice audio** silently onto the Higgsfield video.

```
Your script ──→ ElevenLabs TTS ──→ voice.mp3 ──┐
                                                 ├──→ ffmpeg merge ──→ final.mp4
Visual-only prompt ──→ Higgsfield ──→ raw.mp4 ──┘
```

**Result:** your avatar in any scene (In Car, Studio, Rooftop, anywhere), delivering any script, with a cloned voice — no products, no restrictions.

---

## What You Need

| Requirement | Notes |
|-------------|-------|
| Python 3.10+ | `python3 --version` |
| ffmpeg | `brew install ffmpeg` / `apt install ffmpeg` |
| Higgsfield CLI | `pip3 install higgsfield` then `higgsfield auth login` |
| Higgsfield account | higgsfield.ai — Marketing Studio avatar + scene UUIDs |
| ElevenLabs account | elevenlabs.io — cloned voice ID + API key |
| Telegram bot | @BotFather on Telegram → /newbot |

---

## Quick Setup (AI-Assisted — Recommended)

If you're using **Claude Code**, **VS Code with the Claude Code extension**, or **OpenAI Codex**, just open this project and say:

> "Set up this project for me"

The AI will read `CLAUDE.md` and walk you through the entire setup interactively — asking for your avatar ID, scenes, API keys, and configuring everything automatically.

---

## Manual Setup

```bash
# 1. Clone the repo
git clone https://github.com/prodcastmediaa-cyber/Cracked-Marketing-Studio-UGC.git
cd Cracked-Marketing-Studio-UGC

# 2. Run setup (installs dependencies, creates config.py)
bash setup.sh

# 3. Fill in your keys
nano config.py

# 4. Log in to Higgsfield
higgsfield auth login

# 5. Start the bot
bash start_bot.sh
```

---

## Config Reference

```python
# Your AI character's display name (shown in bot messages)
CHARACTER_NAME = "YourCharacterName"

# Higgsfield Marketing Studio → Avatars → open your avatar → copy UUID
CHARACTER_AVATAR_ID = "your-avatar-uuid"

# Scenes: name shown on bot buttons → Higgsfield setting UUID
# Get UUIDs: Marketing Studio → Settings → open setting → copy UUID
SCENES = {
    "🚗 In Car":   "fdfa032c-801f-4602-8dfd-1162b0f8c9c9",  # built-in Higgsfield preset
    "🏠 Studio":   "your-studio-uuid",
    "🌆 Rooftop":  "your-rooftop-uuid",
}

# ElevenLabs: elevenlabs.io → Profile → API Keys
ELEVENLABS_API_KEY = "your-elevenlabs-api-key"

# ElevenLabs: Voices → open your cloned voice → copy Voice ID
CHARACTER_VOICE_ID = "your-voice-id"

# Telegram: @BotFather → /newbot → copy token
TELEGRAM_BOT_TOKEN = "your-bot-token"

# Telegram: send /start to your bot → copy the chat ID shown
TELEGRAM_CHAT_ID = "your-chat-id"
```

---

## Bot Usage

| Action | How |
|--------|-----|
| New video | Tap **🎬 New Video** |
| Pick scene | Inline buttons appear (In Car / Studio / etc.) |
| Send script | Type or paste your script in chat |
| Get video | Bot generates and sends video (~60s) |
| Retry | Tap **🔄 Retry same script** under any video |
| Delete job | Tap **🗑 Delete** |
| Check status | Tap **📊 Status** or `/status` |

---

## File Structure

```
Cracked-Marketing-Studio-UGC/
├── CLAUDE.md            ← AI assistant setup guide (Claude Code / Codex)
├── bot.py               ← Telegram bot: scene picker + pipeline orchestration
├── ugc_generate.py      ← Core engine: Higgsfield + ElevenLabs TTS + merge
├── voice_swap.py        ← ffmpeg audio merge helper
├── ugc_duration.py      ← Script duration calculator
├── config.example.py    ← Config template (copied to config.py by setup.sh)
├── config.py            ← Your keys (git-ignored, never committed)
├── requirements.txt
├── setup.sh
├── start_bot.sh
└── stop_bot.sh
```

---

## Tips

- **Script length:** Higgsfield caps videos at 15 seconds. Keep scripts under ~30 words for best results. Use `ugc_duration.py` to estimate: `python3 ugc_duration.py "your script here"`
- **More scenes:** Add any number of scenes to `SCENES` in `config.py` — the bot generates buttons automatically. No code changes needed.
- **Clothing variation:** The visual prompt cycles through colours in `CLOTHING_COLOURS` based on a script hash — each video looks slightly different even with the same scene.
- **VPS deployment:** `git clone` → `bash setup.sh` → fill `config.py` → `higgsfield auth login` → `bash start_bot.sh`. View logs: `tail -f bot.log`
- **Multiple characters:** Deploy separate instances with different `config.py` files for each character.

---

## Built With

- [Higgsfield AI](https://higgsfield.ai) — Marketing Studio video generation
- [ElevenLabs](https://elevenlabs.io) — Voice cloning + TTS
- [python-telegram-bot](https://python-telegram-bot.org) — Telegram bot framework
- [ffmpeg](https://ffmpeg.org) — Audio/video merge
