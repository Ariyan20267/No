import sys
import subprocess
import os

# ==================== ০. স্বয়ংক্রিয় ডিপেন্ডেন্সি ইনস্টলার ====================
REQUIRED_PACKAGES = {
    "telebot": "pyTelegramBotAPI",
    "requests": "requests",
    "urllib3": "urllib3"
}

def install_dependencies():
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            print(f"📦 প্যাকেজ ইনস্টল করা হচ্ছে: {pip_name}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name, "--quiet"])

install_dependencies()

# ==================== মডিউল ইমপোর্ট ====================
import re
import time
import html
import random
import threading
import requests
import urllib3
import telebot
from telebot.types import (
    ChatPermissions,
    ReactionTypeEmoji
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== ১. কনফিগারেশন ====================
BOT_TOKEN = "8768727708:AAF62zTgGvjX5TrYQJsR8X1zGZ3yMwuZrMY"  # আপনার বটের টোকেন
BOT_USERNAME = "Boo0ooo_bot"   # @ ছাড়া বটের ইউজারনেম দিন
KEY_FILE = "gemini_key.txt"

# 🚀 আপনার কাঙ্ক্ষিত আল্ট্রা-ফাস্ট অরিজিনাল মডেল
WORKING_MODEL = "models/gemini-flash-lite-latest"

BOT_NAME = "𝐙𝐀𝐑𝐀"
ADMIN_NAME = "আরিয়ান"
SUPER_ADMIN_IDS = [6805684286]  # প্রধান এডমিন আইডি

CODE_DIR = "generated_projects"
os.makedirs(CODE_DIR, exist_ok=True)

# ইউজার ওয়ার্নিং ট্র্যাকার
user_warnings = {}

REACTIONS = ["❤️", "🔥", "✨", "🥰", "⚡", "💅", "💎", "🌸", "👑"]

# ==================== ২. ১২০+ গালি ও স্ল্যাং ডিকশনারি ====================
BAD_WORDS = [
    # বাংলা গালি
    "মাদারচোদ", "চুদা", "চোদ", "খানকি", "খানকির পোলা", "খানকির ছেলে", "মাগীর পোলা", 
    "মাগী", "শুয়োরের বাচ্চা", "শুওর", "কুত্তার বাচ্চা", "কুত্তা", "বেশ্যা", "বাল", 
    "বোকাচোদা", "গাঞ্জাখোর", "হারামি", "ভোদাই", "ভোদাইমোদা", "লুচ্চা", "লুচ্চামি", 
    "চুদমারানি", "রাঁড়ি", "পোদ", "পোদমারানি", "লেবড়া", "নটি", "নটির পোলা", "খচ্চর",
    "চুদিস", "চুদে", "চোদাবো", "চুদবানি", "গুদের", "গুদ", "নেড়ে", "মাগীর",

    # বাংলিশ গালি
    "maderchod", "mc", "bc", "bhodaimoda", "chudmarani", "khankir pola", "khanki", 
    "magir pola", "magi", "shala", "shali", "gandu", "bainchod", "harami", "bal", 
    "chuda", "choda", "chudani", "bogachoda", "kutta", "kuttar bacha", "podmarani", 
    "chod", "behaiya", "bessha", "randi", "randir pola", "madarchod", "suor", 
    "suorer bacha", "banchod", "fokirni", "khankir chele", "bokachoda", "lund", 
    "bur", "bura", "chudis", "chudbo", "gud", "putki", "balsal", "chodao",

    # ইংরেজি গালি
    "fuck", "fucker", "fucking", "bitch", "bastard", "asshole", "dick", "pussy", 
    "cunt", "motherfucker", "slut", "whore", "nigger", "cock", "bullshit", "prick", 
    "retard", "fag", "faggot", "scumbag", "blowjob", "dumbass", "nigga", "hoe"
]

# ==================== ৩. ইনবক্স ও স্প্যাম ফিল্টার ====================
SPAM_PATTERNS = [
    r'\b(i[nb]box|ইনবক্স|ইনবক্সে)\b',
    r'\b(dm\s*me|dm\s*koro|dm\s*korun|check\s*dm|pm\s*me)\b',
    r'(inbox\s*asho|inbox\s*a\s*asho|inbox\s*koro|ib\s*asho|ib\s*te\s*asho)',
    r'(পার্সোনালে\s*আসো|পার্সোনাল\s*মেসেজ|ইনবক্সে\s*আসেন|মেসেজ\s*দেন|ইনবক্স\s*কর)',
    r'(massage\s*dao|message\s*dao|msg\s*dao|come\s*inbox)',
    r'(like\s*sell|লাইক\s*সেল|follower\s*sell|ফলোয়ার\s*সেল)',
    r'(id\s*sell|আইডি\s*সেল|page\s*sell|পেজ\s*সেল|group\s*sell)',
    r'(coin\s*sell|dollar\s*sell|ডলার\s*সেল|ডলার\s*কিনবো|কয়েন\s*সেল)',
    r'(টাকা\s*ইনকাম|free\s*recharge|free\s*taka|ইনকাম\s*করুন|টাকা\s*লাগবে)'
]

URL_REGEX = re.compile(
    r'(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|tg://\S+|bit\.ly/\S+)', 
    re.IGNORECASE
)

# ==================== ৪. লোডার ও পারমিশন ====================

def load_gemini_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

GEMINI_API_KEY = load_gemini_key()
bot = telebot.TeleBot(BOT_TOKEN)
BOT_INFO = bot.get_me()

def is_chat_admin(chat_id, user_id):
    if user_id in SUPER_ADMIN_IDS:
        return True
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['creator', 'administrator']
    except Exception:
        return False

# ==================== ৫. স্টাইলিশ ডিজাইন বক্স ====================

def get_warning_box(user_mention: str, reason: str, warn_count: int) -> str:
    return (
        "╔═══════════════════════════════╗\n"
        "║      ⚠️ <b>গ্রুপ সতর্কবার্তা</b> ⚠️\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 <b>ব্যবহারকারী:</b> {user_mention}\n"
        f"║ 🚫 <b>কারণ:</b> {reason}\n"
        f"║ ⚠️ <b>সতর্কতা:</b> [{warn_count}/2]\n"
        "╠═══════════════════════════════╣\n"
        "║ 📢 <i>গ্রুপের নিয়ম মেনে চলুন।</i>\n"
        "║ আর একবার ভুল করলে <b>১ ঘণ্টার জন্য মিউট</b>!\n"
        "╚═══════════════════════════════╝"
    )

def get_mute_box(user_mention: str, reason: str) -> str:
    return (
        "╔═══════════════════════════════╗\n"
        "║        🔇 <b>মিউট নোটিশ (MUTED)</b> 🔇\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 <b>ব্যবহারকারী:</b> {user_mention}\n"
        f"║ 🚫 <b>কারণ:</b> {reason} (পুনরাবৃত্তি)\n"
        "║ ⏳ <b>শাস্তি:</b> ১ ঘণ্টার জন্য মিউট!\n"
        "╠═══════════════════════════════╣\n"
        "║ 💡 ১ ঘণ্টা পর আপনি স্বয়ংক্রিয়ভাবে কথা\n"
        "║ বলার সুযোগ পাবেন। গ্রুপ শান্ত রাখুন।\n"
        "╚═══════════════════════════════╝"
    )

def get_unmute_box(user_mention: str) -> str:
    return (
        "╔═══════════════════════════════╗\n"
        "║        🔊 <b>আনমিউট নোটিফিকেশন</b> 🔊\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 <b>ব্যবহারকারী:</b> {user_mention}\n"
        "║ ✅ <b>অবস্থা:</b> আপনার শাস্তির মেয়াদ শেষ!\n"
        "╠═══════════════════════════════╣\n"
        "║ 🌸 স্বাগতম আবার! দয়া করে আর গ্রুপের কোনো\n"
        "║ নিয়ম ভঙ্গ করবেন না সোনা। 🥰\n"
        "╚═══════════════════════════════╝"
    )

def create_stylish_ai_box(header, body, footer=""):
    box = f"╭── ✧ <b>{header}</b> ✧ ──╮\n│\n"
    for line in body.strip().split("\n"):
        box += f"│ {line}\n"
    if footer:
        box += f"│\n├── <i>{footer}</i>\n"
    box += "╰──────────────────────────╯"
    return box

# ==================== ৬. অটো আনমিউট ব্যাকগ্রাউন্ড ====================

def auto_unmute_worker(chat_id, user_id, user_mention):
    time.sleep(3600)
    try:
        bot.restrict_chat_member(
            chat_id, user_id,
            permissions=ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True,
                can_send_polls=True
            )
        )
        if chat_id in user_warnings and user_id in user_warnings[chat_id]:
            user_warnings[chat_id][user_id] = 0

        bot.send_message(chat_id, get_unmute_box(user_mention), parse_mode="HTML")
    except Exception as e:
        print(f"Auto Unmute Error: {e}")

# ==================== ৭. আল্ট্রা-ফাস্ট জিমিনি এআই ইঞ্জিন ====================

def ask_gemini_ai(user_prompt, user_name, file_type=None):
    global GEMINI_API_KEY
    if not GEMINI_API_KEY:
        return "আমার API Key সেট করা নেই সোনা! এডমিন বাবুকে বলো /setkey দিয়ে চাবিটা দিতে! 🥺"

    # অরিজিনাল ফাস্ট মডেল ইউআরএল
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}

    if file_type:
        prompt_instruction = (
            f"তুমি একজন সেরা সফটওয়্যার ডেভেলপার যার নাম '{BOT_NAME}'। "
            f"ইউজার '{user_name}' একটি সম্পূর্ণ {file_type.upper()} কোড প্রজেক্ট চেয়েছে। "
            f"তুমি সম্পূর্ণ, সুন্দর, এবং ১০০% নির্ভুল কোড লিখে দিবে। "
            f"উত্তরের শুরুতে অবশ্যই ফাইলের নাম লিখবে: [FILENAME: project_name.{file_type}] "
            f"এবং পুরো কোডটি ```{file_type} এবং ``` কোড ব্লকের ভেতরে রাখবে।"
        )
        max_tokens = 3000
    else:
        prompt_instruction = (
            f"তোমার নাম '{BOT_NAME}'। তুমি {user_name}-এর অত্যন্ত আদুরে, মিষ্টি ও রোমান্টিক বন্ধু এবং {ADMIN_NAME} ভাইয়ের অ্যাসিস্ট্যান্ট। "
            f"কথা হবে খাঁটি বাংলা ও ছোট (১-২ লাইনে)। কোনো বড় প্রশ্নের ক্ষেত্রে সর্বোচ্চ ১০ লাইনে মিষ্টি করে বুঝিয়ে দেবে।"
        )
        max_tokens = 180

    full_prompt = f"{prompt_instruction}\n\nইউজার {user_name} বলেছে: \"{user_prompt}\"\n\nউত্তর:"
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": max_tokens}
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15, verify=False)
        data = res.json()
        if res.status_code == 200 and 'candidates' in data and data['candidates']:
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"Gemini API Error: {e}")

    # কোনো কারণে গুগল লেট করলে ইনস্ট্যান্ট উত্তর (বট আটকে থাকবে না)
    return f"আরে আমার {user_name} বাবু! বলো তো আমি তোমাকে কীভাবে হেল্প করতে পারি? 🥰✨"

# ==================== ৮. ফাস্ট কোড ফাইল জেনারেটর ====================

def format_loading_view(user_name: str, percent: int, bar: str, lights: str) -> str:
    return (
        f"💖 আপনার জন্য কোডিং আমি রেডি করতেছি, একটু অপেক্ষা করুন <b>{user_name}</b> বাবু... 🥰✨\n\n"
        f"⏳ <b>অগ্রগতি:</b> <code>[{bar}] {percent}%</code> {lights}"
    )

def handle_code_generation(chat_id, user_name, reply_to_id, prompt_text, file_type):
    initial_text = format_loading_view(user_name, 25, "██░░░░░░░░", "🔴 🔵")
    loading_msg = bot.send_message(chat_id, initial_text, parse_mode="HTML")

    ai_state = {"code": "", "completed": False}

    def fetch_ai_code():
        ai_state["code"] = ask_gemini_ai(prompt_text, user_name, file_type=file_type)
        ai_state["completed"] = True

    threading.Thread(target=fetch_ai_code, daemon=True).start()

    def animation_process():
        # আল্ট্রা-ফাস্ট ট্রানজিশন (দেরি হবে না)
        steps = [
            (55, "█████░░░░░", "🔵 🟣 🟢"),
            (85, "████████░░", "🟣 🟢 🟡")
        ]

        for percent, bar, lights in steps:
            if ai_state["completed"]:
                break
            time.sleep(0.3)
            try:
                bot.edit_message_text(
                    format_loading_view(user_name, percent, bar, lights),
                    chat_id=chat_id,
                    message_id=loading_msg.message_id,
                    parse_mode="HTML"
                )
            except Exception:
                pass

        wait_counter = 0
        while not ai_state["completed"] and wait_counter < 30:
            time.sleep(0.2)
            wait_counter += 1

        try:
            bot.edit_message_text(
                format_loading_view(user_name, 100, "██████████", "✨ 💎 👑"),
                chat_id=chat_id,
                message_id=loading_msg.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

        raw_code = ai_state["code"]

        fname_match = re.search(r'\[FILENAME:\s*([a-zA-Z0-9_\-\.]+)\.(py|html)\]', raw_code, re.IGNORECASE)
        filename = f"{fname_match.group(1)}.{fname_match.group(2).lower()}" if fname_match else f"project_{int(time.time())}.{file_type}"

        code_match = re.search(rf'```(?:{file_type})?\s*([\s\S]*?)```', raw_code, re.IGNORECASE)
        pure_code = code_match.group(1).strip() if code_match else raw_code.strip()

        # নন-এম্পটি সেফগার্ড
        if len(pure_code) < 10:
            if file_type == "html":
                pure_code = "<!DOCTYPE html>\n<html lang='bn'>\n<head>\n<meta charset='UTF-8'>\n<title>Website</title>\n<style>body{font-family:sans-serif;background:#0f172a;color:#fff;text-align:center;padding:50px;}</style>\n</head>\n<body>\n<h1>✨ ওয়েবসাইট প্রজেক্ট সফলভাবে প্রস্তুত!</h1>\n</body>\n</html>"
            else:
                pure_code = f"# -*- coding: utf-8 -*-\n# তৈরি করেছে {BOT_NAME}\n\ndef main():\n    print('✨ পাইথন প্রজেক্ট সফলভাবে প্রস্তুত!')\n\nif __name__ == '__main__':\n    main()\n"

        file_path = os.path.join(CODE_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(pure_code)

        caption = (
            f"╭── 💎 <b>কোড ফাইল তৈরি সম্পন্ন</b> 💎\n"
            f"│ 👤 <b>অনুরোধকারী:</b> {user_name}\n"
            f"│ 📁 <b>ফাইল:</b> <code>{filename}</code>\n"
            f"│ ⚡ <b>ফরম্যাট:</b> {file_type.upper()} (১০০% ভেরিফাইড)\n"
            f"│ 🌸 <i>{BOT_NAME} এর পক্ষ থেকে উপহার 🥰</i>\n"
            f"╰──────────────────────────╯"
        )

        try:
            with open(file_path, "rb") as doc:
                bot.send_document(chat_id, document=doc, caption=caption, reply_to_message_id=reply_to_id, parse_mode="HTML")
            bot.delete_message(chat_id, loading_msg.message_id)
        except Exception as err:
            bot.edit_message_text(f"❌ এরর: {err}", chat_id=chat_id, message_id=loading_msg.message_id)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    threading.Thread(target=animation_process, daemon=True).start()

# ==================== ৯. কমান্ড হ্যান্ডলার ====================

@bot.message_handler(commands=['setkey'])
def set_key(message):
    global GEMINI_API_KEY
    if not (message.from_user.id in SUPER_ADMIN_IDS):
        return

    key = message.text.replace('/setkey', '').strip()
    if not key:
        bot.reply_to(message, "এডমিন বাবু, এভাবে লিখুন: `/setkey YOUR_KEY`")
        return

    with open(KEY_FILE, "w", encoding="utf-8") as f:
        f.write(key)
    GEMINI_API_KEY = key
    bot.reply_to(message, "✅ <i>Gemini API Key সফলভাবে যুক্ত হয়েছে!</i>", parse_mode="HTML")

# ==================== ১০. সেন্ট্রাল মেসেজ কন্ট্রোলার ====================

@bot.message_handler(func=lambda msg: True, content_types=['text', 'forward_date'])
def central_handler(message):
    try:
        chat_id = message.chat.id
        chat_type = message.chat.type
        user = message.from_user
        if not user or user.is_bot:
            return

        user_id = user.id
        user_name = html.escape(user.first_name or "বন্ধু")
        user_mention = f'<a href="tg://user?id={user_id}">{user_name}</a>'
        text = (message.text or "").strip()
        lower_text = text.lower()
        user_is_admin = is_chat_admin(chat_id, user_id)

        # ১. সাধারণ মেসেজে অটো রিঅ্যাকশন
        try:
            bot.set_message_reaction(chat_id, message.message_id, [ReactionTypeEmoji(random.choice(REACTIONS))], is_big=False)
        except Exception:
            pass

        # ২. গ্রুপ সিকিউরিটি ফিল্টার (এডমিনদের জন্য ১০০% ছাড়)
        if chat_type in ['group', 'supergroup'] and not user_is_admin:
            violation_reason = None

            if message.forward_date or message.forward_from or message.forward_from_chat:
                violation_reason = "গ্রুপে কোনো কিছু ফরোয়ার্ড করা সম্পূর্ণ নিষেধ!"

            elif URL_REGEX.search(text):
                violation_reason = "গ্রুপে যেকোনো ধরনের লিংক শেয়ার করা সম্পূর্ণ নিষেধ!"

            elif any(re.search(r'(?i)\b' + re.escape(w) + r'\b', lower_text) for w in BAD_WORDS):
                violation_reason = "অশালীন ভাষা ও গালিগালাজ ব্যবহার করা হয়েছে!"

            elif any(re.search(pat, lower_text, re.IGNORECASE) for pat in SPAM_PATTERNS):
                violation_reason = "ইনবক্সে ডাকা, আইডি/লাইক বিক্রি বা স্প্যামিং নিষেধ!"

            elif len(text) > 450:
                violation_reason = "অতিরিক্ত বড় মেসেজ দিয়ে গ্রুপ জ্যাম করা নিষেধ!"

            elif message.entities:
                for ent in message.entities:
                    if ent.type == "mention":
                        m_name = text[ent.offset:ent.offset + ent.length].replace("@", "")
                        if m_name.lower() != BOT_USERNAME.lower() and m_name.lower() != BOT_INFO.username.lower():
                            violation_reason = "অন্যান্য বট বা অন্য কারো আইডি মেনশন করা নিষেধ!"
                            break

            # 🛑 নিয়ম ভাঙলে শাস্তি
            if violation_reason:
                try:
                    bot.delete_message(chat_id, message.message_id)
                except Exception:
                    pass

                if chat_id not in user_warnings:
                    user_warnings[chat_id] = {}
                user_warnings[chat_id][user_id] = user_warnings[chat_id].get(user_id, 0) + 1
                count = user_warnings[chat_id][user_id]

                if count == 1:
                    bot.send_message(chat_id, get_warning_box(user_mention, violation_reason, 1), parse_mode="HTML")
                elif count >= 2:
                    try:
                        bot.restrict_chat_member(
                            chat_id, 
                            user_id, 
                            until_date=int(time.time()) + 3600, 
                            permissions=ChatPermissions(can_send_messages=False)
                        )
                        bot.send_message(chat_id, get_mute_box(user_mention, violation_reason), parse_mode="HTML")
                        threading.Thread(target=auto_unmute_worker, args=(chat_id, user_id, user_mention), daemon=True).start()
                    except Exception as err:
                        print(f"Mute Error: {err}")
                return

        # ==================== ১১. স্মার্ট এআই ও কোড ট্রিগার লজিক ====================
        
        # কোডিং চাওয়া হয়েছে কি না চেক
        code_words = ["কোড", "code", "html", "পাইথন", "python", "বানাও", "বানিয়ে দাও", "বানিয়ে দাও", "স্ক্রিপ্ট", "script", "ওয়েবসাইট", "website"]
        is_code_requested = any(w in lower_text for w in code_words)

        # সাধারণ ডাকার নাম
        triggers = ["জারা", "যারা", "zara", "বট", "bot", "আরিয়ান", "আরিয়ান", "ariyan", "এডমিন", "admin", "help", "সাহায্য", "হেল্প"]
        is_called = any(re.search(r'(?i)\b' + re.escape(t) + r'\b', lower_text) for t in triggers)
        is_reply_to_bot = (message.reply_to_message and message.reply_to_message.from_user.id == BOT_INFO.id)
        is_private = (chat_type == 'private')

        # বট কখন সক্রিয় হবে:
        # ১. ইনবক্সে মেসেজ দিলে
        # ২. বটকে রিপ্লাই দিলে
        # ৩. গ্রুপে নাম ধরে ডাকলে
        # ৪. যেকেউ কোড চাইলে (সরাসরি কোড দিলেও কাজ করবে)
        # ৫. এডমিন কথা বললে
        if is_private or is_reply_to_bot or is_called or is_code_requested or (user_is_admin and is_called):

            # ক) ওয়েবসাইট / HTML কোডিং
            html_keywords = ["html", "ওয়েবসাইট", "website", "web page", "ল্যান্ডিং পেজ", "css"]
            if any(k in lower_text for k in html_keywords) and is_code_requested:
                handle_code_generation(chat_id, user_name, message.message_id, text, file_type="html")
                return

            # খ) পাইথন কোডিং
            if is_code_requested:
                handle_code_generation(chat_id, user_name, message.message_id, text, file_type="py")
                return

            # গ) শুধু নাম ধরে ডাকলে কিউট বাংলা রেসপন্স
            clean_word = re.sub(r'[^\w\s]', '', lower_text).strip()
            if clean_word in ["জারা", "যারা", "zara", "বট", "bot", "এডমিন", "admin", "আরিয়ান", "ariyan"]:
                resp = (
                    f"হ্যাঁ <b>{user_name}</b> সোনা! ✨\n"
                    f"আমি আপনাকে কীভাবে সাহায্য করতে পারি বলুন? 🥰\n"
                    f"<i>(আপনার কী কোড বা তথ্য লাগবে বলুন, আমি প্রস্তুত!)</i>"
                )
                bot.reply_to(message, create_stylish_ai_box(f"{BOT_NAME} আপনার পাশে 💖", resp), parse_mode="HTML")
                return

            # ঘ) সাধারণ চ্যাট (১-২ সেকেন্ডে সুপার ফাস্ট উত্তর)
            bot.send_chat_action(chat_id, 'typing')
            ai_reply = ask_gemini_ai(text, user_name, file_type=None)
            
            # ফুটার সিস্টেম: এডমিন হলে 'পরিচালনায় আরিয়ান', অন্যথায় ইউজারের নাম
            if user_is_admin or user_id in SUPER_ADMIN_IDS:
                custom_footer = f"পরিচালনায়: {ADMIN_NAME} ভাই 👑"
            else:
                custom_footer = f"সেবায়: {user_name} 🌸"

            box_resp = create_stylish_ai_box(f"{BOT_NAME} এর উত্তর ✨", html.escape(ai_reply), custom_footer)
            bot.reply_to(message, box_resp, parse_mode="HTML")

    except Exception as e:
        print(f"Error in Central Handler: {e}")

# ==================== মেইন রানার ====================
print(f"⚡ {BOT_NAME} (Fast Lite Model & Coding Engine) ১০০% সচল হয়ে চালু হয়েছে!")
bot.infinity_polling(skip_pending=True)
