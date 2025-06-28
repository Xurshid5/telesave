import os
import asyncio
import shutil
import instaloader
from yt_dlp import YoutubeDL
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import Router

from fastapi import FastAPI
import uvicorn
import threading
from dotenv import load_dotenv

# .env faylni yuklaymiz
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Aiogram
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# FastAPI
app = FastAPI()

# --- Yuklab olish funksiyalari ---

async def download_instagram_media(url: str):
    try:
        loader = instaloader.Instaloader(dirname_pattern="downloads", save_metadata=False, download_comments=False)
        shortcode = url.strip("/").split("/")[-1]
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target="")
        for file in os.listdir("downloads"):
            if file.endswith((".mp4", ".jpg", ".jpeg", ".png")):
                return os.path.join("downloads", file)
    except Exception as e:
        print(f"❌ Instagramdan yuklashda xatolik: {e}")
        return None

async def download_youtube_media(url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt'
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        print(f"❌ YouTubedan yuklashda xatolik: {e}")
        return None

async def download_tiktok_media(url: str):
    return await download_youtube_media(url)

# --- Komandalar ---
@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("👋 Salom! Link yuboring. Men siz uchun videoni yuklab beraman.\n📥 Instagram, YouTube yoki TikTok linklari.")

@router.message()
async def download_handler(message: types.Message):
    url = message.text.strip()
    progress = await message.answer("⏳ Yuklanmoqda...")

    if "instagram.com" in url:
        file_path = await download_instagram_media(url)
    elif "youtube.com" in url or "youtu.be" in url:
        file_path = await download_youtube_media(url)
    elif "tiktok.com" in url:
        file_path = await download_tiktok_media(url)
    else:
        await progress.edit_text("❌ Iltimos, faqat Instagram, YouTube yoki TikTok linkini yuboring.")
        return

    if file_path and os.path.exists(file_path):
        file = FSInputFile(file_path)
        if file_path.endswith((".mp4", ".mov")):
            await message.answer_video(file)
        elif file_path.endswith((".jpg", ".jpeg", ".png")):
            await message.answer_photo(file)
        elif file_path.endswith(".mp3"):
            await message.answer_audio(file)

        try:
            os.remove(file_path)
            shutil.rmtree("downloads", ignore_errors=True)
        except Exception as e:
            print(f"⚠️ Faylni o‘chirishda xatolik: {e}")

        await progress.delete()
    else:
        await progress.edit_text("⚠️ Yuklab bo‘lmadi. Link to‘g‘riligini tekshiring yoki cookies.txt faylini tekshiring.")

# --- FastAPI endpoint ---
@app.get("/")
async def status():
    return {"status": "Bot is running"}

# --- Ishga tushirish funksiyalari ---
async def start_bot():
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

def run_bot():
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("⛔ Bot to‘xtatildi.")

# --- Asosiy ishga tushirish ---
if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    run_bot()
