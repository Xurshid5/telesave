import os
import asyncio
import shutil
import instaloader
from yt_dlp import YoutubeDL
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from aiogram import Router

TOKEN = "8177754909:AAFPySKYPSVhcHs2gZRMoRfoxI4ciJnQF7w"  # O'zingizni tokeningiz bilan almashtiring

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# 📥 Instagram video, rasm va stories yuklash funksiyasi
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

# 📥 YouTube video yoki audio yuklash
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

# 📥 TikTok video yuklash (simple yondashuv)
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

@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("👋 Salom! Instagram, YouTube va TikTok videolarini yuklab beruvchi botga xush kelibsiz.\n\n📥 Video havolasini yuboring.")

@router.message()
async def handle_media_request(message: types.Message):
    url = message.text.strip()

    # Yuklanmoqda... xabari
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

        # Mediani jo'natish
        if media_path.endswith((".mp4", ".mov", ".avi")):
            await message.answer_video(media_file)
        elif media_path.endswith((".jpg", ".jpeg", ".png")):
            await message.answer_photo(media_file)
        elif media_path.endswith(".mp3"):
            await message.answer_audio(media_file)

        # Yuklangan faylni o'chirish
        try:
            os.remove(media_path)
        except Exception as e:
            print(f"⚠️ Faylni o‘chirishda xato: {e}")

        # Yuklangan papkani tozalash
        try:
            shutil.rmtree("downloads")
        except Exception:
            pass

        # "Yuklanmoqda..." xabarini o'chirish
        await progress_message.delete()
    else:
        await progress_message.edit_text("⚠️ Yuklab bo‘lmadi. Linkni tekshirib, qayta urinib ko‘ring.")

# Botni ishga tushirish
async def main():
    dp.include_router(router)
    print("🤖 Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
