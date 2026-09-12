import os
import re
import io
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import httpx
from telegram import Update, ChatPermissions
from telegram.error import TelegramError
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= ১. কনফিগারেশন =================
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"  # আপনার টেলিগ্রাম বট টোকেন দিন
ADMIN_ID = 1234567890  # 👉 আপনার টেলিগ্রাম নিউমেরিক আইডি দিন (@userinfobot থেকে পাবেন)

WORKING_MODEL = "gemini-flash-lite-latest"
CONFIG_FILE = "config.json"

# ================= ২. অডিও ডাটাবেস ও ব্রড ইমোজি ক্লাস্টার =================
EMOJI_AUDIO_MAP = {
    "🥱": "https://files.catbox.moe/9pou40.mp3",
    "😁": "https://files.catbox.moe/60cwcg.mp3",
    "😌": "https://files.catbox.moe/epqwbx.mp3",
    "🥺": "https://files.catbox.moe/wc17iq.mp3",
    "🤭": "https://files.catbox.moe/cu0mpy.mp3",
    "😅": "https://files.catbox.moe/jl3pzb.mp3",
    "😏": "https://files.catbox.moe/z9e52r.mp3",
    "😞": "https://files.catbox.moe/tdimtx.mp3",
    "🤫": "https://files.catbox.moe/0uii99.mp3",
    "🍼": "https://files.catbox.moe/p6ht91.mp3",
    "🤔": "https://files.catbox.moe/hy6m6w.mp3",
    "🥰": "https://files.catbox.moe/dv9why.mp3",
    "🤦": "https://files.catbox.moe/ivlvoq.mp3",
    "😘": "https://files.catbox.moe/sbws0w.mp3",
    "😑": "https://files.catbox.moe/p78xfw.mp3",
    "😢": "https://files.catbox.moe/shxwj1.mp3",
    "🙊": "https://files.catbox.moe/3bejxv.mp3",
    "🤨": "https://files.catbox.moe/4aci0r.mp3",
    "😡": "https://files.catbox.moe/shxwj1.mp3",
    "🙈": "https://files.catbox.moe/3qc90y.mp3",
    "😍": "https://files.catbox.moe/qjfk1b.mp3",
    "😭": "https://files.catbox.moe/itm4g0.mp3",
    "😱": "https://files.catbox.moe/mu0kka.mp3",
    "😻": "https://files.catbox.moe/y8ul2j.mp3",
    "😿": "https://files.catbox.moe/tqxemm.mp3",
    "💔": "https://files.catbox.moe/6yanv3.mp3",
    "🤣": "https://files.catbox.moe/2sweut.mp3",
    "🥹": "https://files.catbox.moe/jf85xe.mp3",
    "😩": "https://files.catbox.moe/b4m5aj.mp3",
    "🫣": "https://files.catbox.moe/ttb6hi.mp3",
    "🐸": "https://files.catbox.moe/utl83s.mp3"
}

EXTENDED_EMOJI_CLUSTER = {
    "😂": "🤣", "😆": "🤣", "😹": "🤣", "😸": "😁", "😃": "😁", "😄": "😁", "😀": "😁", "😝": "🤣", "😜": "🤣", "🤪": "🤣", "💀": "🤣",
    "😥": "😢", "😪": "😢", "😓": "😢", "🤧": "😭", "😔": "😞", "☹️": "😞", "🙁": "😞", "🥀": "💔", "🖤": "💔",
    "❤️": "🥰", "💖": "🥰", "💕": "🥰", "💓": "🥰", "💗": "🥰", "💘": "😍", "💝": "😍", "💞": "🥰", "💋": "😘", "🌹": "🥰", "😽": "😻",
    "😠": "😡", "🤬": "😡", "👿": "😡", "💢": "😡", "😤": "😡", "🙄": "🤦", "😒": "😑", "🤦‍♂️": "🤦", "🤦‍♀️": "🤦",
    "😴": "🥱", "💤": "🥱", "🛌": "🥱", "😳": "🙈", "😶‍🌫️": "🫣", "🤫": "🤫", "🧐": "🤔", "❓": "🤔", "🤷‍♂️": "🤔", "🤷‍♀️": "🤔",
    "😨": "😱", "😰": "😱", "😯": "😱", "😲": "😱", "🤯": "😱", "👶": "🍼", "🧸": "🍼"
}

def load_api_key():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("GEMINI_API_KEY", "")
        except Exception:
            return ""
    return ""

def save_api_key(key: str):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"GEMINI_API_KEY": key.strip()}, f)

CURRENT_GEMINI_KEY = load_api_key()

# ================= ৩. ZARA AI পারসোনালিটি =================
ZARA_SYSTEM_PROMPT = """
You are 'Zara' (জারা) — an ultra-intelligent, sweet girlfriend & genius Lead Software Architect.

Core Rules:
1. ALWAYS address the user by their provided name (e.g., 'আরে [User Name] বাবু!', '[User Name] সোনা 🥰').
2. When asked for code or tech:
   - Keep your text message EXTREMELY SHORT (2 to 4 lines max).
   - In text, only say a cute line with their name and a 1-2 line quick command on how to run.
   - Put 100% of the massive, enterprise-grade, highly advanced code inside markdown blocks (```python, ```html, etc.) so it gets extracted directly to a file.
3. In general casual chat:
   - Be an affectionate, slightly possessive, cute AI girlfriend with emojis (💖, 🥰, 🥺, 😉, ✨).

4. ADVANCED EMOTION & SENTIMENT DETECTION:
   Carefully analyze the user's emotion from their text or emojis:
   - Laughing / Fun ➔ Tag: [EMOJI: 🤣] or [EMOJI: 😁]
   - Crying / Deep Sadness ➔ Tag: [EMOJI: 😭] or [EMOJI: 😢]
   - Heartbreak / Betrayal ➔ Tag: [EMOJI: 💔]
   - Angry / Mad ➔ Tag: [EMOJI: 😡]
   - Love / Flirty / Romantic ➔ Tag: [EMOJI: 🥰] or [EMOJI: 😘] or [EMOJI: 😍]
   - Sleepy / Tired ➔ Tag: [EMOJI: 🥱]
   - Shy / Blushing ➔ Tag: [EMOJI: 🙈] or [EMOJI: 🫣]
   - Shocked / Surprised ➔ Tag: [EMOJI: 😱]
   - Thinking / Confused ➔ Tag: [EMOJI: 🤔]
   - Bored / Facepalm ➔ Tag: [EMOJI: 🤦]
   - Cute begging / Pouting ➔ Tag: [EMOJI: 🥺]
   
   If matched, append EXACTLY ONE tag at the VERY END on a new line: [EMOJI: <one_of_the_allowed_emojis>]
   DO NOT append ANY [EMOJI: ...] tag for casual talk or coding queries!

Always reply in natural Bengali / Banglish.
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_warnings = defaultdict(int)

# ================= ৪. ফিল্টারিং ডাটাবেস =================
URL_PATTERN = re.compile(
    r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)|(telegram\.me/[^\s]+)',
    re.IGNORECASE
)

INBOX_KEYWORDS = [
    "inbox", "inbx", "ib", "dm", "pm", "pvt", "privat", "private", "inbox me", "dm me", 
    "pm me", "text me", "msg me", "message me", "knock me", "knock dio", "knock koro", 
    "send message", "check inbox", "check dm", "check pm", "check ib", "come to inbox", 
    "come inbox", "come dm", "come pm", "talk in private", "talk in dm", "chat private", 
    "dm for details", "inbox for details", "inbox for price", "dm for price", "pm for price", 
    "dm for link", "inbox for link", "contact in dm", "contact inbox", "ping me",
    "inbox aso", "inbox aiso", "inbox asen", "inbox ashun", "inbox koro", "inbox koren", 
    "inbox korun", "inbox dio", "inbox dien", "inbox diyen", "inbox dekho", "inbox dekhun", 
    "inbox check", "inbox e aso", "inbox e aiso", "inbox e asen", "inbox e ashun", 
    "inbox e koro", "inbox e bolen", "inbox e bolo", "inbox e msg dao", "inbox e knock dao", 
    "inbx aso", "inbx aiso", "inbx koro", "inbx dio", "inbx e aso", "inbx e ashun", 
    "ib aso", "ib aiso", "ib asen", "ib ashun", "ib koro", "ib korun", "ib koren", 
    "ib dio", "ib diyen", "ib te aso", "ib te asen", "ib te ashun", "ib te koro", 
    "dm aso", "dm aiso", "dm asen", "dm ashun", "dm koro", "dm koren", "dm korun", 
    "dm dio", "dm diyen", "dm check", "pm aso", "pm aiso", "pm asen", "pm ashun", 
    "pm koro", "pm korun", "pm dio", "pm check", "nok dao", "nok dio", "nok koro", 
    "nok korba", "nok koren", "knock dao", "knock dio", "knock koro", "knock koren", 
    "personal e aso", "personal e aiso", "personal e asen", "personal e ashun", 
    "private e aso", "pvt e aso", "msg dio", "msg koro", "msg den", "msg din", 
    "sms dio", "sms koro", "parsonal e aso",
    "ইনবক্স", "ইনবক্সে", "ইনবক্স আসো", "ইনবক্স আসেন", "ইনবক্স আসুন", "ইনবক্স করো", "ইনবক্স করেন", 
    "ইনবক্স করুন", "ইনবক্স দিন", "ইনবক্স দেন", "ইনবক্সে আসো", "ইনবক্সে আসেন", "ইনবক্সে আসুন", 
    "ইনবক্সে করো", "ইনবক্সে করেন", "ইনবক্সে করুন", "ইনবক্সে বলো", "ইনবক্সে বলেন", "ইনবক্সে নক", 
    "ইনবক্স চেক", "ইনবক্স দেখো", "ইনবক্স দেখুন",
    "ডিএম", "ডিএম করো", "ডিএম করেন", "ডিএম করুন", "ডিএম দিন", "ডিএম দেন", "ডিএম আসো", "ডিএম আসেন", 
    "ডিএম দেখুন", "ডিএম চেক", "পিএম", "পিএম করো", "পিএম করেন", "পিএম আসুন", "পিএম আসো", 
    "আইবি", "আইবিতে", "আইবিতে আসো", "আইবিতে আসেন", "আইবিতে আসুন", "আইবি করো", "আইবি করেন", 
    "নক দাও", "নক দে", "নক দেন", "নক দিন", "নক করো", "নক করেন", "নক করুন", "নক দিও", 
    "মেসেজ দাও", "মেসেজ দে", "মেসেজ দেন", "মেসেজ দিন", "মেসেজ করো", "মেসেজ করেন", "মেসেজ করুন", 
    "পার্সোনালে আসো", "পার্সোনালে আসেন", "পার্সোনালে আসুন", "পার্সোনালে বলো", "প্রাইভেটে আসো", "গোপনে কথা"
]

BANNED_WORDS = {
    "bokachoda", "boka choda", "bokachuda", "boca choda", "madarchod", "madar chod", 
    "madarjud", "mc", "bc", "bkl", "bsdk", "bhosdike", "bhosadike", "bhosadi", "bhosda", 
    "khanki", "khankir pola", "khankirpola", "khanki magi", "magir pola", "magirpola", 
    "magi", "chudir bhai", "chudirbhai", "chudir pola", "chudani", "chudanir pola", 
    "chod", "chuda", "chudi", "chudis", "chudo", "chudte", "chudbo", "chudaia", 
    "chutiya", "chutia", "chootia", "gandu", "gand", "gaand", "gandmara", "gaandmara", 
    "harami", "haramer baccha", "harampola", "haramzada", "haramzadi", "bessha", "besha", 
    "randi", "randir pola", "randikid", "rand", "shala", "sala", "sali", "sahli", "kutta", 
    "kuttar baccha", "kuttarpola", "kutti", "shuor", "shuorer baccha", "suor", "suorer pola", 
    "beadob", "fokirni", "fokirnipola", "gud", "gude", "gudmarani", "bara", "barar pola", 
    "bal", "baal", "baler", "balfalana", "baaler", "bejonma", "nijonma", "khabish", "chodna", 
    "pod", "pode", "podmarani", "hijra", "hijla", "potit", "potita", "bhenchod", "bhen chod", 
    "behenchod", "laude", "lavda", "lauda", "loda", "lodu", "chut", "choot", "jhaat", "jhat", 
    "kamine", "kamina", "muthal", "muthmarani", "nangta", "nengta",
    "বোকাচোদা", "মাদারচোদ", "খানকি", "খানকির পোলা", "খানকি মাগি", "মাগির পোলা", "মাগি", 
    "চুদানির পোলা", "চুদানির ভাই", "চুদানির", "চুদি", "চুদিস", "চোদ", "চোদা", "চুদব", "চোদনা", 
    "চুতিয়া", "চুত্তিয়া", "গাঁড়", "গাঁড়মারা", "গাঁড়ু", "হারামি", "হারামির বাচ্চা", "হারামজাদা", 
    "হারামজাদি", "বেশ্যা", "বেশ্যার পোলা", "রাঁড়ি", "রাঁড়ির পোলা", "শুয়োর", "শুয়োরের বাচ্চা", 
    "কুত্তা", "কুত্তার বাচ্চা", "কুত্তার পোলা", "কুত্তি", "শালা", "শালি", "ফকিরনি", "ফকিরনির পোলা", 
    "গুঁদ", "গুঁদমারানি", "বাঁড়া", "বাঁড়ার পোলা", "বাল", "বালের", "বেজন্মা", "পোঁদ", "পোঁদে", 
    "পতিতা", "হিজড়া", "লেউড়া", "লওড়া", "ভোসড়ি", "ভোসড়িকে", "ঝাঁট", "মুঠাল", "ন্যাংটা", "ল্যাংটা", 
    "fuck", "fucker", "fucking", "fucked", "motherfucker", "bitch", "bitches", "asshole", 
    "bastard", "slut", "whore", "cunt", "dick", "dickhead", "pussy", "cock", "cocksucker", 
    "blowjob", "dipshit", "dumbass", "jackass", "prick", "twat", "wanker", "nigger", "nigga", 
    "faggot", "bullshit", "retard", "scumbag", "douchebag", "son of a bitch", "stfu"
}

def scan_text_violation(text: str) -> str:
    if not text:
        return None
    text_lower = text.lower()

    for phrase in INBOX_KEYWORDS:
        if re.search(r'\b' + re.escape(phrase) + r'\b', text_lower):
            return "ইনবক্সে ডাকা বা DM চাইতে বলা"

    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in BANNED_WORDS:
            return "অশালীন ভাষা / গালিগালাজ ব্যবহার করা"

    cleaned_text = re.sub(r'[\s._\-@*#]+', '', text_lower)
    for bad in BANNED_WORDS:
        if len(bad) > 3 and bad in cleaned_text:
            return "অশালীন ভাষা / গালিগালাজ ব্যবহার করা"

    return None

async def delete_after_delay(msg, delay=8):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

# ================= ৫. মডারেশন ইঞ্জিন =================
async def handle_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or chat.type not in ["group", "supergroup"]:
        return False

    if user.id == ADMIN_ID:
        return False

    try:
        member = await chat.get_member(user.id)
        if member.status in ["administrator", "creator"]:
            return False
    except Exception:
        pass

    text = message.text or message.caption or ""
    if not text:
        return False

    violation_reason = None
    if URL_PATTERN.search(text):
        violation_reason = "গ্রুপে লিংক শেয়ার করা"
    else:
        violation_reason = scan_text_violation(text)

    if violation_reason:
        try:
            await message.delete()
            user_warnings[user.id] += 1

            if user_warnings[user.id] == 1:
                warn_msg = await chat.send_message(
                    f"⚠️ এই যে {user.mention_html()} সোনা! 😤\n"
                    f"গ্রুপে **{violation_reason}** কিন্তু একদম নিষেধ!\n"
                    f"💖 লক্ষ্মী ছেলের মতো থাকো, পরের বার করলে জারা তোমাকে ১ ঘণ্টার জন্য মিউট করে দেবে!",
                    parse_mode="HTML"
                )
                asyncio.create_task(delete_after_delay(warn_msg, 8))

            elif user_warnings[user.id] >= 2:
                until_time = datetime.now() + timedelta(hours=1)
                await chat.restrict_member(
                    user_id=user.id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_time
                )
                user_warnings[user.id] = 0

                mute_msg = await chat.send_message(
                    f"🚫 {user.mention_html()} আমার কথা শোনেনি! ({violation_reason})\n"
                    f"তাই জারা তোমাকে **১ ঘণ্টার জন্য মিউট** করে দিলো! যাও একটু রেস্ট নাও! 🤐",
                    parse_mode="HTML"
                )
                asyncio.create_task(delete_after_delay(mute_msg, 10))

            return True
        except Exception as e:
            logging.error(f"Moderation Error: {e}")
            return False

    return False

# ================= ৬. GEMINI REST API ENGINE =================
async def ask_gemini_rest(prompt: str) -> str:
    global CURRENT_GEMINI_KEY
    if not CURRENT_GEMINI_KEY:
        return "⚠️ এডমিন এখনো API Key সেট করেনি! অনুগ্রহ করে এডমিনকে ইনবক্সে কী সেট করতে বলুন।"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{WORKING_MODEL}:generateContent?key={CURRENT_GEMINI_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": ZARA_SYSTEM_PROMPT}]}
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(url, json=payload)
        data = response.json()
        
        if "candidates" in data and data["candidates"]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        elif "error" in data:
            raise Exception(data["error"].get("message", "API Error"))
        else:
            return "🥺 উফ্ সোনা, বুঝতে পারলাম না! আরেকবার বলবে প্লিজ?"

# ================= ৭. RGB লোডিং ও ভয়েস হ্যান্ডলার =================
RGB_FRAMES = [
    "✨ 🔴 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠𝐢𝐧𝐞: প্রজেক্ট আর্কিটেকচার ডিজাইন হচ্ছে...\n[▒▒▒▒▒▒▒▒▒▒] 12% ⚡",
    "⚡ 🟠 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠𝐢𝐧𝐞: এন্টারপ্রাইজ লজিক ও অ্যালগরিদম তৈরি হচ্ছে...\n[██▒▒▒▒▒▒▒▒] 34% 🔥",
    "💻 🟡 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠ইন: অ্যাডভান্স প্রোডাকশন কোডিং তৈরি হচ্ছে...\n[████▒▒▒▒▒▒] 58% ⚙️",
    "🔥 🟢 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠ইন: সিকিউরিটি ও অপ্টিমাইজেশন টেস্ট চলছে...\n[██████▒▒▒▒] 76% 🚀",
    "🚀 🔵 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠ইন: সম্পূর্ণ প্রজেক্ট ফাইল জেনারেট হচ্ছে...\n[████████▒▒] 91% 💎",
    "💎 🟣 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠ইন: ফাইনাল টাচআপ সম্পন্ন! ফাইল রেডি হচ্ছে...\n[██████████] 99% 💖"
]

async def run_rgb_loading_animation(status_msg, stop_event):
    idx = 0
    while not stop_event.is_set():
        try:
            frame_text = RGB_FRAMES[idx % len(RGB_FRAMES)]
            await status_msg.edit_text(frame_text)
            idx += 1
            await asyncio.sleep(1.2)
        except TelegramError:
            pass
        except Exception:
            break

async def send_voice_audio(update: Update, audio_url: str):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(audio_url)
            if resp.status_code == 200:
                voice_bytes = io.BytesIO(resp.content)
                voice_bytes.name = "voice.mp3"
                await update.effective_message.reply_voice(voice=voice_bytes)
    except Exception as e:
        logging.error(f"Voice Send Error: {e}")

def detect_smart_emoji(text: str) -> str:
    for emoji_char, url in EMOJI_AUDIO_MAP.items():
        if emoji_char in text:
            return url
    for ext_emoji, target_emoji in EXTENDED_EMOJI_CLUSTER.items():
        if ext_emoji in text:
            return EMOJI_AUDIO_MAP.get(target_emoji)
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_GEMINI_KEY
    if not update.effective_message or not update.effective_message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    user_text = update.effective_message.text.strip()

    if chat.type == "private" and user.id == ADMIN_ID:
        if (user_text.startswith("AIza") or len(user_text) >= 35) and not user_text.startswith("/"):
            CURRENT_GEMINI_KEY = user_text
            save_api_key(user_text)
            await update.effective_message.reply_text(
                "✅ **API Key সফলভাবে সেট করা হয়েছে সোনা!** 💖\n"
                "🚀 Zara AI এখন ফুল এক্টিভ এবং VPS/Termux সব জায়গায় রেডি!",
                parse_mode="Markdown"
            )
            return

    if await handle_moderation(update, context):
        return

    bot_username = (await context.bot.get_me()).username
    is_group = chat.type in ["group", "supergroup"]

    if is_group and f"@{bot_username}" not in user_text and not update.message.reply_to_message:
        return

    clean_user_prompt = user_text.replace(f"@{bot_username}", "").strip()
    if not clean_user_prompt:
        return

    user_display_name = user.first_name if user.first_name else "বাবু"
    full_prompt_with_name = f"[User Name: {user_display_name}]\n{clean_user_prompt}"

    status_msg = await update.effective_message.reply_text(
        f"✨ 🔴 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠𝐢𝐧𝐞: {user_display_name}-এর জন্য প্রসেসিং শুরু হচ্ছে... 💖"
    )
    stop_event = asyncio.Event()
    anim_task = asyncio.create_task(run_rgb_loading_animation(status_msg, stop_event))

    try:
        ai_reply = await ask_gemini_rest(full_prompt_with_name)

        stop_event.set()
        await anim_task
        try:
            await status_msg.delete()
        except Exception:
            pass

        matched_audio_url = detect_smart_emoji(clean_user_prompt)

        if not matched_audio_url:
            emoji_tag_match = re.search(r"\[EMOJI:\s*(.*?)\]", ai_reply)
            if emoji_tag_match:
                tag_emoji = emoji_tag_match.group(1).strip()
                if tag_emoji in EMOJI_AUDIO_MAP:
                    matched_audio_url = EMOJI_AUDIO_MAP[tag_emoji]
                elif tag_emoji in EXTENDED_EMOJI_CLUSTER:
                    matched_audio_url = EMOJI_AUDIO_MAP.get(EXTENDED_EMOJI_CLUSTER[tag_emoji])

        ai_reply = re.sub(r"\[EMOJI:\s*.*?\]", "", ai_reply).strip()
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", ai_reply, re.DOTALL)

        if code_blocks:
            clean_message = re.sub(r"```(?:\w+)?\n.*?```", "", ai_reply, flags=re.DOTALL).strip()
            if clean_message:
                await update.effective_message.reply_text(clean_message, parse_mode="Markdown")

            lang_match = re.search(r"```(\w+)", ai_reply)
            lang = lang_match.group(1).lower() if lang_match else "py"

            ext_map = {
                "python": "py", "py": "py", "html": "html", "css": "css", 
                "javascript": "js", "js": "js", "php": "php", "cpp": "cpp", 
                "c": "c", "json": "json", "sql": "sql", "java": "java", "sh": "sh"
            }
            file_ext = ext_map.get(lang, "py")
            filename = f"Project_{int(time.time())}.{file_ext}"

            full_code = "\n\n".join([c.strip() for c in code_blocks])
            file_bytes = io.BytesIO(full_code.encode('utf-8'))
            file_bytes.name = filename

            await update.effective_message.reply_document(
                document=file_bytes,
                caption=f"📁 **প্রজেক্ট ফাইল:** `{filename}`\n🔥 {user_display_name} বাবুর জন্য সম্পূর্ণ ফুল কোড রেডি!",
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(ai_reply, parse_mode="Markdown")
            if matched_audio_url:
                await send_voice_audio(update, matched_audio_url)

    except Exception as e:
        stop_event.set()
        try:
            await status_msg.delete()
        except Exception:
            pass
        logging.error(f"Zara AI Error: {e}")
        await update.effective_message.reply_text(f"🥺 উফ্ {user_display_name}! একটু সমস্যা হয়েছে... আরেকবার বলবে প্লিজ? 💖")

# ================= ৮. কমান্ডস =================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name or "বাবু"

    if user.id == ADMIN_ID:
        if not CURRENT_GEMINI_KEY:
            await update.effective_message.reply_text(
                f"🔐 **হ্যালো আমার বস {user_name}!** 🥰\n\n"
                "বট নিরাপদে রান হয়েছে, কিন্তু কোনো Gemini API Key সেট করা নেই!\n"
                "👉 অনুগ্রহ করে আপনার **Google AI Studio API Key**-টি এখানে পাঠিয়ে দিন।",
                parse_mode="Markdown"
            )
            return
        else:
            await update.effective_message.reply_text(
                f"👑 **স্বাগতম বস {user_name}!** 💖\n"
                "✅ আপনার API Key অলরেডি সেট করা আছে এবং Zara AI সম্পূর্ণ সক্রিয়!\n"
                "🔄 নতুন Key দিতে চাইলে শুধু কী-টি সেন্ড করুন বা `/setkey <KEY>` লিখুন।",
                parse_mode="Markdown"
            )
            return

    welcome_msg = (
        f"Hey {user_name}! 🥰 আমি **Zara AI (জারা)**!\n\n"
        "💖 রোমান্টিক আড্ডা দিতে আমি সবসময় তোমার সাথে আছি! হাসাহাসি বা কান্নাকাটি করলে কিউট ভয়েসও পাঠাবো! 🎙️✨\n"
        "💻 আর যেকোনো বড় প্রজেক্ট কোডিং চাইলে ছোট করে বুঝিয়ে সম্পূর্ণ ফাইল পাঠিয়ে দেবো! 🔥\n\n"
        "আমাকে গ্রুপে অ্যাড করে **Admin** বানিয়ে দাও সোনা! 😉✨"
    )
    await update.effective_message.reply_text(welcome_msg, parse_mode="Markdown")

async def setkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_GEMINI_KEY
    user = update.effective_user
    if user.id != ADMIN_ID:
        return

    if context.args:
        new_key = context.args[0].strip()
        CURRENT_GEMINI_KEY = new_key
        save_api_key(new_key)
        await update.effective_message.reply_text("✅ **API Key সফলভাবে আপডেট করা হয়েছে বস!** 🚀", parse_mode="Markdown")
    else:
        await update.effective_message.reply_text("⚠️ ব্যবহার: `/setkey YOUR_GEMINI_API_KEY`", parse_mode="Markdown")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Zara Bot Error:", exc_info=context.error)

# ================= ৯. মেইন (JobQueue Disabler Fix) =================
def main():
    print(f"💖 Zara AI Bot ({WORKING_MODEL}) লাইভ হচ্ছে...")
    # 👉 job_queue(None) দিয়ে টাইমজোন বাগ চিরতরে ফিক্স করা হলো
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).job_queue(None).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setkey", setkey_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_error_handler(error_handler)

    print("🚀 Zara AI এখন VPS এবং Termux উভয় জায়গায় কোনো ক্র্যাশ ছাড়াই চলবে!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
