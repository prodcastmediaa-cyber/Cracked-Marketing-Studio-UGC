"""
bot.py — Cracked Marketing Studio UGC Bot

Flow:
  1. User presses "🎬 New Video" (or types anything)
  2. Bot shows scene selection buttons (In Car / Studio / Rooftop / etc.)
  3. User picks a scene
  4. Bot asks for the script
  5. User types or pastes the script
  6. Higgsfield Marketing Studio generates the visual (visual-only prompt)
  7. ElevenLabs TTS generates the character's voice from the script
  8. ffmpeg merges audio → video sent back to Telegram

Commands:
  /start   — confirm the bot is live
  /status  — see active jobs
  /help    — how to use
"""
import asyncio
import atexit
import glob
import logging
import os
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)
from telegram.request import HTTPXRequest

from config import (
    CHARACTER_NAME,
    OUTPUTS_DIR,
    SCENES,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)

# ── Persistent keyboard ───────────────────────────────────────────────────────

MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["🎬 New Video", "📊 Status"]],
    resize_keyboard=True,
    is_persistent=True,
    input_field_placeholder="Pick a scene first, then type your script...",
)

# ── Logging ───────────────────────────────────────────────────────────────────

_log_handlers = [logging.FileHandler("bot.log")]
if sys.stderr.isatty():
    _log_handlers.append(logging.StreamHandler())

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=_log_handlers,
)
log = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

# ── Single-instance lock ──────────────────────────────────────────────────────

_PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bot.pid")


def _acquire_pid_lock() -> None:
    if os.path.exists(_PID_FILE):
        try:
            with open(_PID_FILE) as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                log.info(f"[pid] Stopping old instance (PID {old_pid})...")
                try:
                    os.kill(old_pid, signal.SIGTERM)
                except ProcessLookupError:
                    old_pid = None
                if old_pid:
                    for _ in range(10):
                        try:
                            os.kill(old_pid, 0)
                            time.sleep(0.5)
                        except ProcessLookupError:
                            break
        except (ValueError, OSError):
            pass

    with open(_PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    def _remove_pid():
        try:
            os.remove(_PID_FILE)
        except FileNotFoundError:
            pass

    atexit.register(_remove_pid)


# ── Globals ───────────────────────────────────────────────────────────────────

_executor = ThreadPoolExecutor(max_workers=3)
_processing: set = set()        # job names currently generating
_stage: dict = {}               # job_name → status string
_lock = threading.Lock()
_loop: asyncio.AbstractEventLoop = None
_app: Application = None

# Per-user state
_awaiting_script: dict = {}     # chat_id → {"name": str, "scene_id": str, "scene_name": str}
_script_cache: dict = {}        # job_name → script (for retry)

_job_counter: int = 0


# ── Helpers ───────────────────────────────────────────────────────────────────

def _next_job_name() -> str:
    global _job_counter
    existing = glob.glob(os.path.join(OUTPUTS_DIR, "ugc", "video*"))
    nums = []
    for p in existing:
        stem = os.path.basename(p)
        if stem.startswith("video") and stem[5:].isdigit():
            nums.append(int(stem[5:]))
    n = (max(nums) + 1) if nums else 1
    _job_counter = max(_job_counter + 1, n)
    return f"video{_job_counter}"


def _has_output(name: str) -> bool:
    return os.path.exists(os.path.join(OUTPUTS_DIR, "ugc", name, "output.mp4"))


def _video_dimensions(path: str) -> tuple:
    import json, subprocess
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "json", path],
        capture_output=True, text=True,
    )
    streams = json.loads(r.stdout).get("streams", [{}])
    return streams[0].get("width", 1080), streams[0].get("height", 1920)


# ── Telegram helpers ──────────────────────────────────────────────────────────

async def _notify(text: str) -> None:
    try:
        await _app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, text=text, parse_mode="Markdown"
        )
    except Exception as e:
        log.error(f"Telegram notify failed: {e}")


async def _safe_edit(query, text: str, keyboard=None) -> None:
    try:
        if query.message.photo:
            await query.edit_message_caption(
                caption=text, parse_mode="Markdown", reply_markup=keyboard
            )
        else:
            await query.edit_message_text(
                text=text, parse_mode="Markdown", reply_markup=keyboard
            )
    except Exception as e:
        log.warning(f"_safe_edit failed: {e}")


# ── Scene picker ──────────────────────────────────────────────────────────────

async def _send_scene_picker(reply_fn, job_name: str) -> None:
    scene_names = list(SCENES.keys())
    rows = []
    for i in range(0, len(scene_names), 2):
        row = [
            InlineKeyboardButton(scene_names[i], callback_data=f"scene:{job_name}:{scene_names[i]}")
        ]
        if i + 1 < len(scene_names):
            row.append(
                InlineKeyboardButton(scene_names[i + 1], callback_data=f"scene:{job_name}:{scene_names[i + 1]}")
            )
        rows.append(row)
    rows.append([InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{job_name}")])

    await reply_fn(
        f"🎬 *New Video — Pick a scene:*\n\n"
        + "\n".join(f"• {name}" for name in scene_names),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def _on_scene_pick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, job_name, scene_name = query.data.split(":", 2)
    scene_id = SCENES.get(scene_name)
    if not scene_id:
        await _safe_edit(query, f"⚠️ Scene `{scene_name}` not found in config.")
        return

    _awaiting_script[TELEGRAM_CHAT_ID] = {
        "name": job_name,
        "scene_id": scene_id,
        "scene_name": scene_name,
    }
    _stage[job_name] = "⏸ Waiting for script"

    await _safe_edit(
        query,
        f"✅ *{scene_name}* selected for `{job_name}`.\n\n"
        f"Now type or paste the script and {CHARACTER_NAME} will deliver it.",
    )


# ── UGC pipeline ─────────────────────────────────────────────────────────────

def _run_ugc(name: str, script: str, scene_id: str) -> str:
    from ugc_generate import generate
    out_dir = os.path.join(OUTPUTS_DIR, "ugc", name)
    os.makedirs(out_dir, exist_ok=True)
    return generate(script, scene_id, out_dir)


async def _do_ugc(name: str, script: str, scene_id: str, scene_name: str) -> None:
    loop = asyncio.get_running_loop()
    with _lock:
        _processing.add(name)
    _stage[name] = "🎬 Generating"

    await _notify(
        f"🎬 *{name}* — Generating {CHARACTER_NAME} in *{scene_name}*...\n\n"
        f"_Higgsfield is rendering the video, then ElevenLabs adds the voice._"
    )

    try:
        out_path = await loop.run_in_executor(_executor, _run_ugc, name, script, scene_id)

        if out_path and os.path.exists(out_path):
            size_mb = os.path.getsize(out_path) / 1_000_000
            width, height = _video_dimensions(out_path)
            retry_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Retry same script", callback_data=f"retry:{name}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"delete:{name}"),
            ]])
            with open(out_path, "rb") as f:
                await _app.bot.send_video(
                    chat_id=TELEGRAM_CHAT_ID,
                    video=f,
                    caption=(
                        f"🎬 *{name}* — Done! ({size_mb:.1f} MB)\n"
                        f"Scene: {scene_name}"
                    ),
                    parse_mode="Markdown",
                    supports_streaming=True,
                    width=width,
                    height=height,
                    reply_markup=retry_kb,
                )
            _stage[name] = "✅ Done"
        else:
            await _notify(f"❌ *{name}* — Generation finished but output not found. Check logs.")
            _stage[name] = "❌ Failed"

    except Exception as e:
        log.exception(f"[{name}] UGC pipeline error")
        err = str(e)
        _script_cache[name] = script

        if "OUT_OF_CREDITS:Higgsfield" in err:
            msg = f"💳 *{name}* — Out of Higgsfield credits. Top up → higgsfield.ai/billing"
        elif "OUT_OF_CREDITS:ElevenLabs" in err:
            msg = f"💳 *{name}* — Out of ElevenLabs credits. Top up → elevenlabs.io/billing"
        elif "not authenticated" in err.lower():
            msg = f"🔑 *{name}* — Higgsfield not authenticated. Run: `higgsfield auth login`"
        else:
            msg = f"❌ *{name}* — Failed: `{err[:200]}`"

        retry_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Retry", callback_data=f"retry:{name}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"delete:{name}"),
        ]])
        await _app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=msg,
            parse_mode="Markdown",
            reply_markup=retry_kb,
        )
        _stage[name] = "❌ Failed"

    finally:
        with _lock:
            _processing.discard(name)


# ── Message handler (script input) ───────────────────────────────────────────

async def _on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    chat_id = str(update.effective_chat.id)

    # Check keyboard buttons first
    if text == "🎬 New Video":
        name = _next_job_name()
        await _send_scene_picker(update.message.reply_text, name)
        return

    if text == "📊 Status":
        await _on_status(update, context)
        return

    # Check if we're waiting for a script from this user
    pending = _awaiting_script.get(TELEGRAM_CHAT_ID) or _awaiting_script.get(chat_id)
    if pending:
        key = TELEGRAM_CHAT_ID if TELEGRAM_CHAT_ID in _awaiting_script else chat_id
        _awaiting_script.pop(key, None)
        name = pending["name"]
        scene_id = pending["scene_id"]
        scene_name = pending["scene_name"]
        _script_cache[name] = text

        await update.message.reply_text(
            f"🎬 *{name}* — Got it! Generating with {CHARACTER_NAME}'s voice...",
            parse_mode="Markdown",
        )
        asyncio.create_task(_do_ugc(name, text, scene_id, scene_name))
        return

    # No pending state — show scene picker
    name = _next_job_name()
    await _send_scene_picker(update.message.reply_text, name)


# ── Retry / Delete callbacks ──────────────────────────────────────────────────

async def _on_retry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, name = query.data.split(":", 1)

    script = _script_cache.get(name)
    if not script:
        await _safe_edit(
            query,
            f"⚠️ *{name}* — Script not cached. Start a new video instead.",
        )
        return

    import shutil
    shutil.rmtree(os.path.join(OUTPUTS_DIR, "ugc", name), ignore_errors=True)
    with _lock:
        _processing.discard(name)

    # We need the scene from somewhere — store it in cache alongside script
    scene_info = _script_cache.get(f"{name}__scene")
    scene_id = scene_info["id"] if scene_info else list(SCENES.values())[0]
    scene_name = scene_info["name"] if scene_info else list(SCENES.keys())[0]

    await _safe_edit(query, f"🔄 *{name}* — Retrying...")
    asyncio.create_task(_do_ugc(name, script, scene_id, scene_name))


async def _on_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, name = query.data.split(":", 1)

    import shutil
    shutil.rmtree(os.path.join(OUTPUTS_DIR, "ugc", name), ignore_errors=True)
    _script_cache.pop(name, None)
    _script_cache.pop(f"{name}__scene", None)
    _stage.pop(name, None)
    with _lock:
        _processing.discard(name)

    await _safe_edit(query, f"🗑 *{name}* — Deleted.", keyboard=None)
    log.info(f"[{name}] Deleted by user.")


async def _on_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    _, name = query.data.split(":", 1)

    _awaiting_script.pop(TELEGRAM_CHAT_ID, None)
    _stage.pop(name, None)
    with _lock:
        _processing.discard(name)

    await _safe_edit(query, f"❌ Cancelled.", keyboard=None)


# ── Commands ──────────────────────────────────────────────────────────────────

async def _on_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cid = update.effective_chat.id
    scene_list = "\n".join(f"  • {name}" for name in SCENES)
    await update.message.reply_text(
        f"🤖 *{CHARACTER_NAME} UGC Bot is live!*\n\n"
        f"Your chat ID: `{cid}`\n\n"
        f"*Available scenes:*\n{scene_list}\n\n"
        f"Tap *🎬 New Video* to start.",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


async def _on_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    scene_list = "\n".join(f"  • {name}" for name in SCENES)
    await update.message.reply_text(
        f"🤖 *{CHARACTER_NAME} UGC Bot — Help*\n\n"
        "*How it works:*\n"
        "1️⃣ Tap *🎬 New Video*\n"
        f"2️⃣ Pick a scene ({', '.join(SCENES.keys())})\n"
        "3️⃣ Type or paste your script\n"
        f"4️⃣ {CHARACTER_NAME} delivers it — video arrives in ~60s\n\n"
        f"*Available scenes:*\n{scene_list}\n\n"
        "*Commands:*\n"
        "/status — See all active jobs\n"
        "/help — Show this message\n\n"
        "*Tips:*\n"
        "• Scripts under ~30 words work best (Higgsfield max = 15s)\n"
        "• You can retry any video with the same script using the Retry button\n"
        "• Add more scenes in `config.py` → `SCENES` dict",
        parse_mode="Markdown",
    )


async def _on_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    active = len(_processing)
    jobs = [(k, v) for k, v in _stage.items()]

    if not jobs:
        await update.message.reply_text(
            "📭 *No active jobs.*\n\nTap 🎬 New Video to generate one!",
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
        return

    lines = [f"*Job Status* — {active} active\n"]
    for name, stage in sorted(jobs):
        tag = " ⚙️" if name in _processing else ""
        lines.append(f"• `{name}`: {stage}{tag}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    global _loop, _app

    _acquire_pid_lock()
    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN must be set in config.py")

    if not TELEGRAM_CHAT_ID:
        log.warning("TELEGRAM_CHAT_ID not set — send /start to your bot to get it.")

    if not SCENES:
        raise RuntimeError("SCENES dict in config.py is empty — add at least one scene.")

    _loop = asyncio.get_running_loop()

    _request = HTTPXRequest(connection_pool_size=1, http_version="1.1")
    _get_updates_request = HTTPXRequest(connection_pool_size=1, http_version="1.1")
    _app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(_request)
        .get_updates_request(_get_updates_request)
        .build()
    )

    _app.add_handler(CommandHandler("start",  _on_start))
    _app.add_handler(CommandHandler("help",   _on_help))
    _app.add_handler(CommandHandler("status", _on_status))

    _app.add_handler(CallbackQueryHandler(_on_scene_pick, pattern=r"^scene:"))
    _app.add_handler(CallbackQueryHandler(_on_retry,      pattern=r"^retry:"))
    _app.add_handler(CallbackQueryHandler(_on_delete,     pattern=r"^delete:"))
    _app.add_handler(CallbackQueryHandler(_on_cancel,     pattern=r"^cancel:"))

    _app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_text))

    await _app.initialize()
    await _app.start()
    await asyncio.sleep(3)
    await _app.updater.start_polling(drop_pending_updates=True)
    log.info("[bot] Telegram polling started")

    if TELEGRAM_CHAT_ID:
        scene_list = "  ".join(SCENES.keys())
        await _app.bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=(
                f"🚀 *{CHARACTER_NAME} UGC Bot is live!*\n\n"
                f"Scenes ready: {scene_list}\n\n"
                "Tap *🎬 New Video* to start generating."
            ),
            parse_mode="Markdown",
            reply_markup=MAIN_KEYBOARD,
        )
    else:
        log.info("[bot] Waiting for chat ID — send /start to your bot in Telegram.")

    try:
        await asyncio.Event().wait()
    finally:
        await _app.updater.stop()
        await _app.stop()
        await _app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
