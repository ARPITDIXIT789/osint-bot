import telebot
import requests
import json
from colorama import Fore, Style

# === BOT TOKEN ===
BOT_TOKEN = "8285984712:AAHHJHQzkH1HAJ9wZTK4TB1TVtQ8VO8IX7s"
bot = telebot.TeleBot(BOT_TOKEN)

# === YOUR CHANNELS (FIXED) ===
CHANNEL_1 = "@VividYTOfficial"      
CHANNEL_2 = "-1002602851793"        
CHANNEL_3 = "-1002773252709"        

# === YOUR PROTECTED NUMBER ===
MY_NUMBER = "8090544126"

# === API CONFIGURATION ===
API_TOKEN = "NIGHTFALLHUBz"
URL = "https://usesirosint.vercel.app/api/numinfo"

# === CHANNEL MEMBERSHIP CHECK ===
def is_user_member(user_id):
    channels = [CHANNEL_2, CHANNEL_3]
    for channel_id in channels:
        try:
            chat_member = bot.get_chat_member(channel_id, user_id)
            status = chat_member.status
            print(f"✅ {channel_id}: {status}")
            if status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"❌ Error {channel_id}: {e}")
            return False
    print(f"✅ User APPROVED!")
    return True

# === START COMMAND ===
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    print(f"\n🔍 Checking user: {user_id}")
    
    if not is_user_member(user_id):
        join_msg = (
            "🔒 *PEHLE YE 2 CHANNELS JOIN KARO:*\n\n"
            "📢 **Channel 1:** https://t.me/VividYTOfficial\n"
            "📢 **Channel 2:** https://t.me/+Q5VXFHviVoVjZjM9\n\n"
            "✅ *Dono join karo → /start karo*\n\n"
            "🔴 *Credit: ARPITxPROTON*"
        )
        bot.send_message(message.chat.id, join_msg, parse_mode='Markdown', disable_web_page_preview=True)
        return
    
    welcome_text = (
        "🎉 *WELCOME TO OSINT BOT* ✅\n\n"
        "🔍 **10-digit number bhejo**\n"
        "📱 *e.g. 9812345678*\n\n"
        "⚡ Leaked data milega!\n\n"
        "🔴 *Credit: ARPITxPROTON*"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')

# === NUMBER SEARCH ===
def format_as_js(data):
    lines = []
    for key, value in data.items():
        value_str = str(value).replace("'", '"')
        lines.append(f"  {key}: {value_str}")
    return "{\n" + "\n".join(lines) + "\n}"

@bot.message_handler(func=lambda message: True)
def handle_number(message):
    user_id = message.from_user.id
    query = message.text.strip()

    # Channel check
    if not is_user_member(user_id):
        bot.send_message(
            message.chat.id,
            "🚫 *CHANNELS JOIN NHI KIYE!*\n\n"
            "📢 https://t.me/VividYTOfficial\n"
            "📢 https://t.me/+Q5VXFHviVoVjZjM9",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        return

    # **🚫 YOUR NUMBER PROTECTION**
    num = ''.join(c for c in query if c.isdigit())
    if num == MY_NUMBER:
        troll_msg = (
            "😂 **HE IS YOUR FATHER**\n\n"
            "📱 **Number:** `8090544126`\n"
            "👑 **Owner:** ARPITxPROTON\n\n"
            "❌ *PAPA HU BETA TERA!*\n\n"
            "🔴 *Credit: ARPITxPROTON*"
        )
        bot.send_message(message.chat.id, troll_msg, parse_mode='Markdown')
        print(f"🚫 User {user_id} tried to search MY_NUMBER!")
        return

    # Normal validation
    if len(num) != 10:
        bot.send_message(message.chat.id, "⚠️ *10 DIGIT NUMBER BEJO*\n`9812345678`")
        return

    # Searching...
    msg = bot.send_message(message.chat.id, "🔍 *Searching leaks...*")
    
    try:
        params = {"key": API_TOKEN, "num": num}
        resp = requests.get(URL, params=params, timeout=15)
        data = resp.json()

        if not data.get("success"):
            bot.edit_message_text("🚫 *THIS NUMBER DATA NOT AVAILABLE TRY OTHER MOBILE NUMBER*", message.chat.id, msg.message_id)
            return

        results = data.get("result", [])
        if not results:
            bot.edit_message_text("❌ *No leaks found*", message.chat.id, msg.message_id)
            return

        # Remove duplicates
        unique = []
        seen = set()
        for entry in results:
            key = tuple(sorted(entry.items()))
            if key not in seen:
                seen.add(key)
                unique.append(entry)

        # Results
        text = f"🔍 **Results: `{num}`** ({len(unique)} entries)\n\n"
        for i, entry in enumerate(unique, 1):
            js_data = format_as_js(entry)
            text += f"**#{i}:**\n```js\n{js_data}\n```\n\n"

        text += "🔴 *Credit: ARPITxPROTON*"
        bot.edit_message_text(text, message.chat.id, msg.message_id, parse_mode='Markdown')

    except Exception as e:
        bot.edit_message_text(f"❌ Error: {str(e)}", message.chat.id, msg.message_id)

# === RUN BOT ===
if __name__ == "__main__":
    print(f"{Fore.GREEN}🚀 OSINT BOT STARTING...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📢 Channel 1: {CHANNEL_2}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}📢 Channel 2: {CHANNEL_3}{Style.RESET_ALL}")
    print(f"{Fore.RED}🔒 Protected Number: {MY_NUMBER}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✅ READY!{Style.RESET_ALL}")
    
    print("\n" + "="*50)
    bot.infinity_polling()
