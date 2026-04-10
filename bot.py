import os
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler

TOKEN = os.getenv("BOT_TOKEN")

# store files temporarily per user
user_files = {}

# 📥 Receive audio/voice
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.effective_attachment.get_file()

    user_id = update.message.from_user.id
    os.makedirs(f"tmp/{user_id}", exist_ok=True)

    file_path = f"tmp/{user_id}/{file.file_id}.ogg"
    await file.download_to_drive(file_path)

    user_files.setdefault(user_id, []).append(file_path)

    # Buttons
    keyboard = [
        [
            InlineKeyboardButton("+20%", callback_data="1.2"),
            InlineKeyboardButton("+50%", callback_data="1.5"),
            InlineKeyboardButton("+100%", callback_data="2.0"),
        ]
    ]

    await update.message.reply_text(
        f"{len(user_files[user_id])} file(s) ready. Choose boost:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# 🔊 Process audio
async def process_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    factor = query.data  # 1.2 / 1.5 / 2.0

    files = user_files.get(user_id, [])

    for input_path in files:
        output_path = input_path.replace(".ogg", "_out.ogg")

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"volume={factor}",
            output_path
        ]

        subprocess.run(cmd)

        with open(output_path, "rb") as voice_file:
            await query.message.reply_voice(voice=voice_file)

        os.remove(input_path)
        os.remove(output_path)

    user_files[user_id] = []

    await query.message.reply_text("Done ✅")

# 🚀 Run bot
if __name__ == "__main__":
    if not TOKEN:
        print("Error: BOT_TOKEN environment variable not set.")
    else:
        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_audio))
        app.add_handler(CallbackQueryHandler(process_audio))

        print("Bot is starting...")
        app.run_polling()
