import os
import re
import shutil
import asyncio
import threading
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import FSInputFile
from aiogram.filters import Command
from fastapi import FastAPI
from yt_dlp import YoutubeDL
import instaloader
import uvicorn
from dotenv import load_dotenv

# --- Sozlamalar ---
load_dotenv()
TOKEN = os.getenv("TOKEN")
os.makedirs("downloads", exist_ok=True)

# --- Aiogram sozlamalari ---
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# --- FastAPI ---
app = FastAPI()

# --- Yuklab olish funksiyalari ---
async def download_instagram_media(url: str):
    try:
        shortcode_match = re.search(r"/(p|reel|tv)/([a-zA-Z0-9_-]+)", url)
        if not shortcode_match:
            return None
        shortcode = shortcode_match.group(2)
        loader = instaloader.Instaloader(dirname_pattern="downloads", save_metadata=False, download_comments=False)
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target="")
        for file in os.listdir("downloads"):
            if file.endswith((".mp4", ".jpg", ".jpeg", ".png")):
                return os.path.join("downloads", file)
    except Exception as e:
        print(f"❌ Instagramdan yuklashda xatolik: {e}")
        return None

async def download_youtube_media(url: str):
    options = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s'
    }
    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"❌ YouTubedan yuklashda xatolik: {e}")
        return None

async def download_tiktok_media(url: str):
    return await download_youtube_media(url)

# --- Telegram komandalar ---
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Salom! Men YouTube, Instagram yoki TikTok videolarini yuklab beraman. Link yuboring.")

@router.message()
async def handle_link(message: types.Message):
    url = message.text.strip()
    chat_id = message.chat.id
    status = await message.answer("⏳ Yuklanmoqda...")

    if "instagram.com" in url:
        file_path = await download_instagram_media(url)
    elif "youtube.com" in url or "youtu.be" in url:
        file_path = await download_youtube_media(url)
    elif "tiktok.com" in url:
        file_path = await download_tiktok_media(url)
    else:
        await status.edit_text("❌ Faqat Instagram, YouTube yoki TikTok linklarini yuboring.")
        return

    if file_path and os.path.exists(file_path):
        file = FSInputFile(file_path)
        try:
            if file_path.endswith((".mp4", ".mov")):
                await bot.send_video(chat_id, video=file)
            elif file_path.endswith((".jpg", ".jpeg", ".png")):
                await bot.send_photo(chat_id, photo=file)
            elif file_path.endswith(".mp3"):
                await bot.send_audio(chat_id, audio=file)
            else:
                await bot.send_document(chat_id, document=file)
        except Exception as e:
            await bot.send_message(chat_id, f"❌ Fayl yuborishda xatolik: {e}")
        finally:
            os.remove(file_path)
            shutil.rmtree("downloads", ignore_errors=True)
            await status.delete()
    else:
        await status.edit_text("❌ Yuklab bo‘lmadi. Linkni tekshiring.")

# --- FastAPI endpoint ---
@app.get("/")
async def health_check():
    return {"status": "Bot is running ✅"}

# --- Ishga tushirish funksiyalari ---
async def start_bot():
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_bot():
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("⛔ Bot to‘xtatildi.")

# --- Asosiy ---
if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
