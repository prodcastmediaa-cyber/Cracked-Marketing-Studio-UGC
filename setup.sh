#!/usr/bin/env bash
set -e

echo "=== Cracked Marketing Studio UGC — Setup ==="

# 1. Create output folder
mkdir -p outputs/ugc
echo "✓ Output folder created"

# 2. Install Python dependencies
pip3 install -r requirements.txt
echo "✓ Python dependencies installed"

# 3. Copy config template
if [ ! -f config.py ]; then
    cp config.example.py config.py
    echo "✓ config.py created from template"
    echo ""
    echo "⚠️  Open config.py and fill in:"
    echo "    CHARACTER_NAME, CHARACTER_AVATAR_ID"
    echo "    SCENES (add your Higgsfield setting UUIDs)"
    echo "    ELEVENLABS_API_KEY, CHARACTER_VOICE_ID"
    echo "    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID"
else
    echo "✓ config.py already exists — skipping"
fi

# 4. Check ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️  ffmpeg not found. Install it:"
    echo "    macOS:  brew install ffmpeg"
    echo "    Ubuntu: sudo apt install ffmpeg"
else
    echo "✓ ffmpeg found"
fi

# 5. Check higgsfield CLI
if ! command -v higgsfield &>/dev/null; then
    echo "⚠️  Higgsfield CLI not found. Install it:"
    echo "    pip3 install higgsfield"
    echo "    higgsfield auth login"
else
    echo "✓ Higgsfield CLI found"
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Fill in config.py"
echo "  2. Run: higgsfield auth login"
echo "  3. Run: bash start_bot.sh"
