import logging
import requests
import json
import time
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from colorama import Fore, init
import os

init(autoreset=True)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('osint-bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Bot token and API key
TOKEN = "8285984712:AAHHJHQzkH1HAJ9wZTK4TB1TVtQ8VO8IX7s"
API_KEY = "NIGHTFALLHUBz"
LEAK_API = "https://usesirosint.vercel.app/api/numinfo"
OWNER_NUMBER = "8090544126"

# Channel IDs (chat_id format)
CHANNELS = ["@VividYTOfficial", "-1002602851793", "-1002773252709"]

# User stats tracking
user_stats = {}
active_users = set()

def is_user_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is member of required channels"""
    for channel in CHANNELS:
        try:
            member = context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def query_leak_api(phone: str) -> str:
    """Query leak API with retries"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"number": phone}
    
    for attempt in range(3):
        try:
            response = requests.post(LEAK_API, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"API request failed (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
    return "❌ API Error - Try again later"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with channel join links"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "No username"
    
    # Track new user
    if user_id not in user_stats:
        user_stats[user_id] = {"username": username, "first_seen": time.time(), "queries": 0}
        active_users.add(user_id)
        logger.info(f"New user: {username} (ID: {user_id})")
    
    # Check membership
    if not is_user_member(user_id, context):
        await update.message.reply_text(
            "🔒 **Join these channels first:**\n\n"
            "👑 [VividYT Official](https://t.me/VividYTOfficial)\n"
            "🔥 [Channel 2](https://t.me/+Q5VXFHviVoVjZjM9)\n"
            "📢 [Channel 3](https://t.me/joinchat/XXXXX)  <!-- Update this link -->\n\n"
            "/start after joining",
            parse_mode='Markdown'
        )
        return
    
    stats_text = f"👥 **Active Users:** {len(active_users)}\n📊 **Total Users:** {len(user_stats)}"
    await update.message.reply_text(
        f"🚀 **OSINT Bot Active!**\n\n"
        f"{stats_text}\n\n"
        "📱 Send 10-digit Indian number\n"
        "💎 **Powered by ARPITxPROTON**",
        parse_mode='Markdown'
    )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 10-digit number messages"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Extract digits only
    digits = ''.join(c for c in message_text if c.isdigit())
    
    # Validate 10-digit Indian number
    if len(digits) != 10 or not digits.isdigit():
        await update.message.reply_text("❌ Send exactly 10-digit Indian number")
        return
    
    phone = digits
    
    # Owner protection troll
    if phone == OWNER_NUMBER:
        await update.message.reply_text("😂 **HE IS YOUR FATHER**\nDon't mess with owner!")
        return
    
    # Update user stats
    if user_id not in user_stats:
        user_stats[user_id] = {"username": update.effective_user.username or "Unknown", "first_seen": time.time(), "queries": 0}
    user_stats[user_id]["queries"] += 1
    active_users.add(user_id)
    
    # Show processing
    processing_msg = await update.message.reply_text("🔍 **Querying leaks...**")
    
    # Query API
    result = query_leak_api(phone)
    
    # Update stats in response
    total_queries = sum(user["queries"] for user in user_stats.values())
    await processing_msg.edit_text(
        f"📱 **Number:** `{phone}`\n"
        f"👥 **Active Users:** {len(active_users)}\n"
        f"📈 **Total Queries:** {total_queries}\n\n"
        f"```json\n{result}\n```\n\n"
        f"💎 **ARPITxPROTON**",
        parse_mode='Markdown'
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin stats command"""
    user_id = update.effective_user.id
    if str(user_id) not in [OWNER_NUMBER]:  # Add owner Telegram ID here
        return
    
    total_users = len(user_stats)
    total_queries = sum(user["queries"] for user in user_stats.values())
    active_count = len(active_users)
    
    stats_msg = (
        f"📊 **Bot Stats**\n\n"
        f"👥 **Total Users:** {total_users}\n"
        f"🔥 **Active Users:** {active_count}\n"
        f"📈 **Total Queries:** {total_queries}\n\n"
        f"**Top Users:**\n"
    )
    
    # Top 5 users by queries
    sorted_users = sorted(user_stats.items(), key=lambda x: x[1]["queries"], reverse=True)[:5]
    for uid, data in sorted_users:
        stats_msg += f"• {data['username']}: {data['queries']} queries\n"
    
    await update.message.reply_text(stats_msg, parse_mode='Markdown')

def main():
    """Main bot function with AWS-safe polling"""
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & 
        filters.Regex(r'^\d{10}$|.*\d{10}.*') &
        ~filters.Regex(r'^/'),
        handle_number
    ))
    
    logger.info("🚀 Bot starting with user stats tracking...")
    logger.info(f"📊 Initial stats: {len(user_stats)} users, {len(active_users)} active")
    
    # AWS-safe polling with restart loop
    while True:
        try:
            print(Fore.GREEN + "🤖 Bot polling started...")
            application.run_polling(
                interval=3,
                timeout=30,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Polling error: {e}")
            print(Fore.RED + f"❌ Error: {e}")
            print(Fore.YELLOW + "⏳ Restarting in 10 seconds...")
            time.sleep(10)

if __name__ == '__main__':
    main()
