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
from dotenv import load_dotenv  # <-- Qo‘shildi


import os

import telegram
from telegram.ext import Updater

# Yangi parametr qo'shing
updater = Updater(token='YOUR_BOT_TOKEN', use_context=True)
bot = updater.bot

# Avvalgi webhooklarni o'chirish (agar webhook ishlatgan bo'lsangiz)
bot.delete_webhook()

# Polling ni boshlash
updater.start_polling(
    drop_pending_updates=True,  # Qolgan updatelarni o'tkazib yuborish
    timeout=10,
    clean=True
)

# Agar Flask/FastAPI ishlatayotgan bo'lsangiz:
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running", 200  # UptimeRobot 200 status kutadi

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)  # Render faqat 8000-portni qo'llab-quvvatlaydi


# Telegram bot tokeni .env dan olinadi
TOKEN = os.getenv("TOKEN")  # <-- O‘zgartirildi

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

app = FastAPI()  # FastAPI ilovasi


# --- Yuklash funksiyalari ---

async def download_instagram_media(url: str):
    loader = instaloader.Instaloader(dirname_pattern="downloads", save_metadata=False, download_comments=False)
    try:
        shortcode = url.split("/")[-2]
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
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path
    except Exception as e:
        print(f"❌ YouTubedan yuklashda xatolik: {e}")
        return None

async def download_tiktok_media(url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info_dict)
            return file_path
    except Exception as e:
        print(f"❌ TikTokdan yuklashda xatolik: {e}")
        return None

# --- Telegram bot komandalar va handlerlari ---

@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Salom! Instagram, YouTube va TikTok videolarini yuklab beruvchi botga xush kelibsiz.\n\n"
        "📥 Video havolasini yuboring."
    )

@router.message()
async def handle_media_request(message: types.Message):
    url = message.text.strip()

    # "Yuklanmoqda..." xabarini yuboramiz
    progress_message = await message.answer("⏳ Yuklanmoqda, biroz kuting...")

    if "instagram.com" in url:
        media_path = await download_instagram_media(url)
    elif "youtube.com" in url or "youtu.be" in url:
        media_path = await download_youtube_media(url)
    elif "tiktok.com" in url:
        media_path = await download_tiktok_media(url)
    else:
        await progress_message.edit_text("❌ Iltimos, Instagram, YouTube yoki TikTok havolasini yuboring.")
        return

    if media_path:
        media_file = FSInputFile(media_path)

        # Mediani yuborish
        if media_path.endswith((".mp4", ".mov", ".avi")):
            await message.answer_video(media_file)
        elif media_path.endswith((".jpg", ".jpeg", ".png")):
            await message.answer_photo(media_file)
        elif media_path.endswith(".mp3"):
            await message.answer_audio(media_file)

        # Fayl va papkani o'chirish
        try:
            os.remove(media_path)
            shutil.rmtree("downloads")
        except Exception as e:
            print(f"⚠️ Faylni o‘chirishda xato: {e}")

        # "Yuklanmoqda..." xabarini o'chirish
        await progress_message.delete()
    else:
        await progress_message.edit_text("⚠️ Yuklab bo‘lmadi. Linkni tekshirib, qayta urinib ko‘ring.")

# --- Bot ishga tushirish funksiyasi ---

async def main():
    dp.include_router(router)
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

# --- FastAPI route (ping uchun) ---

@app.get("/")
async def root():
    return {"status": "Bot is running"}

# --- FastAPI va botni paralel ishga tushirish ---

def start_bot():
    asyncio.run(main())

def start_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # FastAPI va Telegram botni alohida ipda ishga tushiramiz
    threading.Thread(target=start_api).start()
    start_bot()
