#!/usr/bin/env python3
import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import telebot
from telebot import types
import python-dotenv

# Load .env (keeping old hardcoded as backup)
python_dotenv.load_dotenv()

# Config - env vars with old hardcoded fallback
BOT_TOKEN = os.getenv('BOT_TOKEN', '8285984712:AAHHJHQzkH1HAJ9wZTK4TB1TVtQ8VO8IX7s')
CHANNEL_1 = os.getenv('CHANNEL_1', '-1002602851793')  # Only 1 channel now
OWNER_NUMBER = os.getenv('OWNER_NUMBER', '8090544126')
LEAK_API_URL = os.getenv('LEAK_API_URL', 'https://usesirosint.vercel.app/api/numinfo')
LEAK_API_KEY = os.getenv('LEAK_API_KEY', 'NIGHTFALLHUBz')
COOLDOWN_SECONDS = int(os.getenv('COOLDOWN_SECONDS', '30'))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler('osint-bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)

# Cooldown tracking
user_cooldowns = {}

# Session with retries
session = requests.Session()
retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount('http://', adapter)
session.mount('https://', adapter)

def is_user_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_1, user_id)
        return member.status not in ['left', 'kicked']
    except:
        return False

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.from_user.id
    if not is_user_member(user_id):
        bot.reply_to(message, """📢 <b>Channel 1:</b> https://t.me/+Q5VXFHviVoVjZjM9

🔒 Join first then /start! 👇""", parse_mode='HTML')
        return
    
    bot.reply_to(message, f"""
✅ <b>OSINT Bot Ready!</b>

📱 Send 10-digit number
⏱️ Cooldown: {COOLDOWN_SECONDS}s
🔒 Owner protected: {OWNER_NUMBER}
    """, parse_mode='HTML')

@bot.message_handler(func=lambda message: message.text and message.text.isdigit() and len(message.text) == 10)
def handle_number(message):
    user_id = message.from_user.id
    number = message.text
    
    # Owner troll
    if number == OWNER_NUMBER:
        bot.reply_to(message, "🤡 <b>HE IS YOUR FATHER</b> 🤡\n\nBoss ko mat tang karo! 😈", parse_mode='HTML')
        return
    
    # Member check
    if not is_user_member(user_id):
        bot.reply_to(message, """📢 <b>Channel 1:</b> https://t.me/+Q5VXFHviVoVjZjM9

❌ Join first!""", parse_mode='HTML')
        return
    
    # Cooldown
    now = time.time()
    if user_id in user_cooldowns and now - user_cooldowns[user_id] < COOLDOWN_SECONDS:
        remaining = int(COOLDOWN_SECONDS - (now - user_cooldowns[user_id]))
        bot.reply_to(message, f"⏳ {remaining}s wait karo!")
        return
    user_cooldowns[user_id] = now
    
    msg = bot.reply_to(message, "🔍 Checking leaks...")
    
    try:
        resp = session.get(LEAK_API_URL, params={'number': number, 'key': LEAK_API_KEY}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get('leaks'):
            bot.edit_message_text(f"✅ <b>Clean!</b>\n\n<code>{number}</code>\nNo leaks found!", 
                                msg.chat.id, msg.message_id, parse_mode='HTML')
        else:
            leaks = data['leaks'][:5]
            result = f"🚨 <b>LEAKS!</b>\n\n<code>{number}</code>\n\n"
            for leak in leaks:
                result += f"• {leak.get('site', 'Unknown')}\n"
            if len(data['leaks']) > 5:
                result += f"\n+{len(data['leaks'])-5} more"
            bot.edit_message_text(result, msg.chat.id, msg.message_id, parse_mode='HTML')
            
    except Exception as e:
        logger.error(f"Error {number}: {e}")
        bot.edit_message_text("❌ API error! Try later.", msg.chat.id, msg.message_id)

if __name__ == '__main__':
    print("✅ READY!")
    logger.info("Bot starting with DELAYED polling...")
    
    while True:
        try:
            print("🔄 Polling...")
            bot.polling(none_stop=True, interval=2, timeout=25, long_polling_timeout=25)
        except Exception as e:
            logger.error(f"Polling crash: {e}")
            print("💤 Restarting in 10s...")
            time.sleep(10)
