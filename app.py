import os
import asyncio
import shutil
from yt_dlp import YoutubeDL
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import FSInputFile
from fastapi import FastAPI
import uvicorn
import threading
from dotenv import load_dotenv

# .env faylini yuklaymiz
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Aiogram bot obyektlari
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# FastAPI ilova
app = FastAPI()

# Yuklash funktsiyasi (universal, cookie bilan)
async def download_video(url: str):
    filename = "downloads/%(title)s.%(ext)s"
    ydl_opts = {
        'outtmpl': filename,
        'cookies': 'cookies.txt',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'quiet': True
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            return filepath
    except Exception as e:
        print(f"❌ Yuklashda xatolik: {e}")
        return None

# Start komandasi
@router.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("👋 Botga xush kelibsiz! foydalanuvchi\n📥 Instagram, YouTube yoki TikTok link yuboring.")

# Link kelganda ishlovchi funksiya
@router.message()
async def handle_media(message: types.Message):
    url = message.text.strip()
    msg = await message.answer("⏳ Yuklanmoqda...")

    if any(domain in url for domain in ["instagram.com", "youtube.com", "youtu.be", "tiktok.com"]):
        path = await download_video(url)
        if path and os.path.exists(path):
            file = FSInputFile(path)
            if path.endswith((".mp4", ".mov")):
                await message.answer_video(file)
            elif path.endswith((".jpg", ".jpeg", ".png")):
                await message.answer_photo(file)
            await msg.delete()
            try:
                os.remove(path)
                shutil.rmtree("downloads", ignore_errors=True)
            except Exception as e:
                print(f"⚠️ Tozalashda xato: {e}")
        else:
            await msg.edit_text("⚠️ Yuklab bo‘lmadi. Link to‘g‘riligini tekshiring.")
    else:
        await msg.edit_text("❌ Faqat Instagram, YouTube yoki TikTok link yuboring.")

# FastAPI tekshiruv marshruti
@app.get("/")
async def root():
    return {"status": "Bot is running"}

# Telegram botni ishga tushirish
async def start_bot():
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(start_bot())

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Bot va API paralel ishga tushadi
if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    run_bot()
