# AI Assistant Setup Guide — Cracked Marketing Studio UGC

This file is read by Claude Code, VS Code + Claude extension, OpenAI Codex, and similar AI coding assistants. When a user says "set up this project", "help me get started", or similar, follow this guide exactly.

---

## What This Project Does

Generates product-free talking-head UGC videos using Higgsfield Marketing Studio + ElevenLabs TTS. The key technique: the user's script never goes to Higgsfield (bypasses product injection and content filtering). Instead, the script goes to ElevenLabs TTS and the voice is merged onto the video with ffmpeg.

---

## For the AI Assistant: Setup Flow

When the user asks to set up this project, guide them through these steps **in order**, asking for one thing at a time. Do not dump all questions at once.

### Step 1 — Check system dependencies

Run these checks and fix anything missing before proceeding:

```bash
python3 --version   # needs 3.10+
ffmpeg -version     # if missing: brew install ffmpeg (mac) or apt install ffmpeg (linux)
higgsfield --version  # if missing: pip3 install higgsfield
```

If `higgsfield` is missing, install it and tell the user to log in:
```bash
pip3 install higgsfield
higgsfield auth login
```

### Step 2 — Install Python dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3 — Create config.py

```bash
cp config.example.py config.py
```

### Step 4 — Ask the user for their config values (one at a time)

Ask each question separately and wait for the answer before moving to the next.

**Question 1: Character name**
> "What is your AI character's name? (This is the name shown in all bot messages, e.g. Aria, Mia, Sofia)"

**Question 2: Higgsfield Avatar ID**
> "What is your Higgsfield Marketing Studio Avatar ID?
> How to find it: higgsfield.ai → Marketing Studio → Avatars → click your avatar → copy the UUID from the URL or the settings panel."

**Question 3: Scenes**
> "Which Higgsfield scenes do you want to use? The 'In Car' scene is built in (UUID: fdfa032c-801f-4602-8dfd-1162b0f8c9c9).
> Do you want to add more scenes? If yes, go to: higgsfield.ai → Marketing Studio → Settings → open a setting → copy its UUID. Tell me the scene name and UUID for each one you want."

Add them to the SCENES dict in config.py. Keep "In Car" as the default unless the user removes it.

**Question 4: ElevenLabs API key**
> "What is your ElevenLabs API key?
> How to find it: elevenlabs.io → click your profile (top right) → API Keys → copy."

**Question 5: ElevenLabs Voice ID**
> "What is your character's ElevenLabs Voice ID?
> How to find it: elevenlabs.io → Voices → click your cloned voice → the Voice ID is shown in the voice settings panel."

**Question 6: Telegram Bot Token**
> "What is your Telegram Bot Token?
> How to get one if you don't have it: open Telegram → search for @BotFather → send /newbot → follow the steps → copy the token it gives you."

**Question 7: Telegram Chat ID**
> "What is your Telegram Chat ID?
> How to find it: start your new bot in Telegram by sending it /start — the bot will reply with your chat ID. If the bot hasn't started yet, we'll get this after launching."

### Step 5 — Write all values into config.py

After collecting all answers, open `config.py` and fill in every value the user provided. Use the Edit tool to update the file — do not ask the user to do it manually.

Verify the file looks correct before moving on.

### Step 6 — Higgsfield authentication

Ask the user to run:
```bash
higgsfield auth login
```
A browser window will open. Tell them to log in and come back once done.

### Step 7 — Create the outputs folder

```bash
mkdir -p outputs/ugc
```

### Step 8 — Start the bot

```bash
bash start_bot.sh
```

Then tell the user: "Open Telegram and send /start to your bot. It should reply and show the 🎬 New Video button. If it shows your chat ID there, copy it and I'll add it to config.py for you."

If they provide the chat ID at this point, update `TELEGRAM_CHAT_ID` in config.py and restart:
```bash
bash stop_bot.sh && bash start_bot.sh
```

### Step 9 — Test

Tell the user to:
1. Tap **🎬 New Video** in their Telegram bot
2. Pick a scene
3. Type a short script (under 30 words)
4. Wait ~60 seconds for the video

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `higgsfield: not authenticated` | Run `higgsfield auth login` in the terminal |
| `OUT_OF_CREDITS:Higgsfield` | Top up at higgsfield.ai/billing |
| `OUT_OF_CREDITS:ElevenLabs` | Top up at elevenlabs.io/billing |
| Bot not responding | Check `tail -f bot.log` for errors |
| Script too long | Keep under ~30 words; Higgsfield max is 15s |
| No video in Telegram | Check that `TELEGRAM_CHAT_ID` is set in config.py |

---

## Adding More Scenes Later

Tell the user they can add new scenes any time by editing `config.py`:
```python
SCENES = {
    "🚗 In Car":   "fdfa032c-801f-4602-8dfd-1162b0f8c9c9",
    "🏠 Studio":   "their-studio-uuid",
    "🌆 Rooftop":  "their-rooftop-uuid",
    # Add any new scene here — the bot generates buttons automatically
}
```
Then restart: `bash stop_bot.sh && bash start_bot.sh`

---

## VPS Deployment

If the user wants to run this on a server 24/7:
```bash
git clone https://github.com/prodcastmediaa-cyber/Cracked-Marketing-Studio-UGC.git
cd Cracked-Marketing-Studio-UGC
bash setup.sh
# fill in config.py
higgsfield auth login
bash start_bot.sh
# view logs
tail -f bot.log
```

---

## Key Files

| File | Purpose |
|------|---------|
| `bot.py` | Telegram bot — scene picker, script input, pipeline |
| `ugc_generate.py` | Core engine — Higgsfield + ElevenLabs TTS + audio merge |
| `voice_swap.py` | ffmpeg audio merge utility |
| `ugc_duration.py` | Duration calculator — test with `python3 ugc_duration.py "script"` |
| `config.py` | All API keys and settings (never commit this file) |
| `config.example.py` | Template — safe to commit, has no real keys |
