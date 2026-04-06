import os
import logging
import yt_dlp
import aiofiles
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from uuid import uuid4

if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("لم يتم العثور على BOT_TOKEN!")

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

SUPPORTED_SITES = [
    'youtube.com', 'youtu.be',
    'twitter.com', 'x.com',
    'reddit.com', 'facebook.com'
]

def is_supported_url(url):
    return any(site in url.lower() for site in SUPPORTED_SITES)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = """
🎬 **بوت تحميل الفيديوهات**

أرسل رابط فيديو من:
• YouTube
• Twitter / X  
• Reddit
• Facebook
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(('http://', 'https://')):
        return await update.message.reply_text("❌ أرسل رابط صحيح")
    
    if not is_supported_url(url):
        return await update.message.reply_text("❌ موقع غير مدعوم")
    
    wait_msg = await update.message.reply_text("⏳ جاري التحضير...")
    uid = str(uuid4())[:8]
    out_path = f"{DOWNLOAD_PATH}/{uid}"
    
    try:
        ydl_opts = {
            'format': 'best[filesize<50M]/best',
            'outtmpl': f'{out_path}.%(ext)s',
            'quiet': True,
        }
        
        await wait_msg.edit_text("⬇️ جاري التحميل...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'فيديو')
            
            # إيجاد الملف المحمل
            downloaded = None
            for ext in ['mp4', 'mkv', 'webm']:
                f = f"{out_path}.{ext}"
                if os.path.exists(f):
                    downloaded = f
                    break
            
            if downloaded:
                await wait_msg.edit_text("📤 جاري الإرسال...")
                async with aiofiles.open(downloaded, 'rb') as f:
                    video_data = await f.read()
                    await update.message.reply_video(
                        video=video_data, 
                        caption=f"🎬 {title}"
                    )
                os.remove(downloaded)
                await wait_msg.delete()
            else:
                await wait_msg.edit_text("❌ لم يتم العثور على الملف")
                
    except Exception as e:
        logger.error(f"Error: {e}")
        await wait_msg.edit_text(f"❌ خطأ: {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    logger.info("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
