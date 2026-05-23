import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Output folder ──────────────────────────────────────────────────────────────
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# ── Character identity ─────────────────────────────────────────────────────────
# The name shown in all bot messages (e.g. "Bella", "Mia", "Sofia")
CHARACTER_NAME = "YourCharacterName"

# Higgsfield Marketing Studio avatar ID
# How to get it: higgsfield.ai → Marketing Studio → Avatars → open your avatar → copy the UUID
CHARACTER_AVATAR_ID = "YOUR_MARKETING_STUDIO_AVATAR_ID"

# ── Scenes (Higgsfield Marketing Studio settings) ──────────────────────────────
# Each scene is a name → Higgsfield setting UUID pair.
# Users will pick from these via Telegram buttons.
# How to get UUIDs: higgsfield.ai → Marketing Studio → Settings → open setting → copy UUID
SCENES = {
    "🚗 In Car":   "fdfa032c-801f-4602-8dfd-1162b0f8c9c9",  # default "in car" preset
    "🏠 Studio":   "YOUR_STUDIO_SETTING_UUID",
    "🌆 Rooftop":  "YOUR_ROOFTOP_SETTING_UUID",
}

# ── Clothing cycle (optional — visual-only, never sent to Higgsfield as script) ─
# Cycles through these colours based on script hash so each video looks slightly different.
CLOTHING_COLOURS = ["black", "red", "lavender"]

# ── ElevenLabs ─────────────────────────────────────────────────────────────────
# Get your key: elevenlabs.io → Profile → API Keys
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY"

# Your character's cloned voice ID
# elevenlabs.io → Voices → open your cloned voice → copy the Voice ID
CHARACTER_VOICE_ID = "YOUR_ELEVENLABS_VOICE_ID"

# ── Telegram ───────────────────────────────────────────────────────────────────
# Step 1: Message @BotFather on Telegram → /newbot → copy the token below
# Step 2: Start your bot in Telegram, send /start → copy the chat ID shown
TELEGRAM_BOT_TOKEN = ""   # e.g. "7123456789:AAFxxx..."
TELEGRAM_CHAT_ID   = ""   # e.g. "123456789"
