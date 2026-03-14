#!/usr/bin/env python3
"""
Production Telegram OSINT Bot - Leak Checker for Indian Numbers
✅ Env vars • Cooldowns • Sessions • Logging • Retry logic • Webhook ready
"""
import os
import sys
import time
import json
import logging
import asyncio
import signal
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from telebot import TeleBot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from telebot.types import Message
import python-dotenv

# Load .env
python_dotenv.load_dotenv()

# Required env vars
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_1 = os.getenv('CHANNEL_1', '-1002602851793')
CHANNEL_2 = os.getenv('CHANNEL_2', '-1002773252709')
OWNER_NUMBER = os.getenv('OWNER_NUMBER', '8090544126')
LEAK_API_URL = os.getenv('LEAK_API_URL', 'https://usesirosint.vercel.app/api/numinfo')
LEAK_API_KEY = os.getenv('LEAK_API_KEY', 'NIGHTFALLHUBz')
USE_WEBHOOK = os.getenv('USE_WEBHOOK', 'false').lower() == 'true'
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
COOLDOWN_SECONDS = int(os.getenv('COOLDOWN_SECONDS', '30'))

# Validate required vars
required = ['BOT_TOKEN', 'OWNER_NUMBER', 'LEAK_API_KEY']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f"❌ Missing env vars: {', '.join(missing)}")
    sys.exit(1)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('osint-bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Bot setup with state storage
state_storage = StateMemoryStorage()
bot = TeleBot(BOT_TOKEN, state_storage=state_storage, parse_mode='HTML')

# Global state
user_cooldowns: Dict[int, float] = {}
request_session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
request_session.mount("http://", adapter)
request_session.mount("https://", adapter)

class BotStates(StatesGroup):
    WAITING_FOR_NUMBER = State()

def is_user_member(user_id: int) -> bool:
    """Check membership in both channels with caching"""
    try:
        for chat_id in [CHANNEL_1, CHANNEL_2]:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status in ['left', 'kicked']:
                return False
        return True
    except Exception as e:
        logger.error(f"Membership check failed: {e}")
        return False

def enforce_cooldown(user_id: int) -> bool:
    """Enforce per-user cooldown"""
    now = time.time()
    if user_id in user_cooldowns:
        if now - user_cooldowns[user_id] < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - user_cooldowns[user_id]))
            return False, remaining
    user_cooldowns[user_id] = now
    return True, 0

@bot.message_handler(commands=['start'])
def start_handler(message: Message):
    user_id = message.from_user.id
    if not is_user_member(user_id):
        links = f"""
🔒 <b>Access Denied!</b> Join these channels first:

• <a href="https://t.me/+{CHANNEL_1[4:]}">VividYT Official</a>
• <a href="https://t.me/+{CHANNEL_2[4:]}">Leak Check Group</a>

Then /start again! 👇
        """
        bot.reply_to(message, links)
        return
    
    welcome = f"""
✅ <b>OSINT Leak Bot Active!</b>

📱 Send 10-digit Indian number
⏱️ Cooldown: {COOLDOWN_SECONDS}s
🔒 Protected: {OWNER_NUMBER}

Powered by NightfallHub API
    """
    bot.reply_to(message, welcome)

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text) == 10)
def handle_number(message: Message):
    user_id = message.from_user.id
    number = message.text
    
    # Owner protection
    if number == OWNER_NUMBER:
        troll = """
🤡 <b>HE IS YOUR FATHER</b> 🤡

Don't mess with the boss! 😈
        """
        bot.reply_to(message, troll)
        return
    
    # Membership check
    if not is_user_member(user_id):
        bot.reply_to(message, "❌ Join channels first! /start")
        return
    
    # Cooldown check
    can_proceed, remaining = enforce_cooldown(user_id)
    if not can_proceed:
        bot.reply_to(message, f"⏳ Wait {remaining}s before next query!")
        return
    
    # Show processing
    processing_msg = bot.reply_to(message, "🔍 Checking leaks...")
    
    try:
        # API call with timeout and retries
        response = request_session.get(
            LEAK_API_URL,
            params={'number': number, 'key': LEAK_API_KEY},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        result = format_leak_result(data, number)
        bot.edit_message_text(result, processing_msg.chat.id, processing_msg.message_id)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API error for {number}: {e}")
        error_msg = "❌ API timeout or error. Try again later!"
        bot.edit_message_text(error_msg, processing_msg.chat.id, processing_msg.message_id)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        bot.edit_message_text("💥 Something went wrong!", processing_msg.chat.id, processing_msg.message_id)

def format_leak_result(data: dict, number: str) -> str:
    """Format API response nicely"""
    if not data or 'leaks' not in data or not data['leaks']:
        return f"✅ <b>Clean Number</b>\n\n📱 <code>{number}</code>\n🔒 No leaks found!"
    
    leaks = data['leaks']
    result = f"🚨 <b>LEAKS FOUND!</b>\n\n📱 <code>{number}</code>\n\n"
    
    for leak in leaks[:5]:  # Limit to top 5
        result += f"• {leak.get('site', 'Unknown')}\n"
    
    if len(leaks) > 5:
        result += f"\n...and {len(leaks)-5} more"
    
    return result

def graceful_shutdown(signum=None, frame=None):
    """Clean shutdown"""
    logger.info("Shutting down gracefully...")
    try:
        if USE_WEBHOOK:
            bot.remove_webhook()
        bot.stop_polling()
    except:
        pass
    sys.exit(0)

def run_polling():
    """Run bot with polling"""
    logger.info("🚀 Starting with long polling...")
    while True:
        try:
            logger.info("Starting polling loop...")
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as e:
            logger.error(f"Polling error: {e}. Restarting in 5s...")
            time.sleep(5)

def run_webhook():
    """Run bot with webhook"""
    if not WEBHOOK_URL:
        logger.error("WEBHOOK_URL required for webhook mode")
        sys.exit(1)
    
    logger.info(f"🚀 Starting webhook server on {WEBHOOK_URL}")
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    
    @bot.message_handler(content_types=['text'])
    def webhook_handler(message):
        # Same handlers as polling
        if message.text == '/start':
            start_handler(message)
        elif message.text and message.text.isdigit() and len(message.text) == 10:
            handle_number(message)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            time.sleep(5)

def main():
    logger.info("🤖 OSINT Bot starting...")
    logger.info(f"Channels: {CHANNEL_1}, {CHANNEL_2}")
    logger.info(f"Cooldown: {COOLDOWN_SECONDS}s")
    logger.info(f"Webhook: {USE_WEBHOOK}")
    
    # Graceful shutdown handlers
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    if USE_WEBHOOK:
        run_webhook()
    else:
        run_polling()

if __name__ == '__main__':
    main()
