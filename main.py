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
TELEGRAM_BOT_TOKEN = "8526557973:AAFYIh3NcXYbefpFj9An_lic13fFjSyrAqo"
ADMIN_ID = 6805684286

WORKING_MODEL = "gemini-flash-lite-latest"
CONFIG_FILE = "config.json"

admin_states = {}
VOICE_FILE_ID_CACHE = {}

# ================= ২. অডিও ডাটাবেস ও ইমোজি ক্লাস্টার =================
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
    "😴": "🥱", "💤": "🥱", "🛌": "🥱",
    "😳": "🙈", "😶‍🌫️": "🫣", "🤫": "🤫",
    "🧐": "🤔", "❓": "🤔", "🤷‍♂️": "🤔", "🤷‍♀️": "🤔",
    "😨": "😱", "😰": "😱", "😯": "😱", "😲": "😱", "🤯": "😱",
    "👶": "🍼", "🧸": "🍼"
}

TEXT_EMOTION_KEYWORDS = {
    "😭": ["কান্না", "কষ্ট", "চোখে জল", "চোখে পানি", "মন খারাপ", "ভালো নেই", "ভালো লাগতেছে না", "কেঁদে", "কাঁদব", "কাদবো", "cry", "crying", "sad"],
    "💔": ["ব্রেকআপ", "ধোঁকা", "মন ভাঙ", "ছেড়ে গেছ", "কষ্ট দিলি", "প্রতারণা", "breakup", "heartbreak"],
    "🤣": ["হাসি", "মজা পাইলাম", "হাসতে হাসতে", "hahaha", "lol", "lmao", "rofl", "funny", "হিহি", "হাহাহা"],
    "🥰": ["ভালোবাসি", "ভালবাসি", "love you", "উম্মা", "জানু", "অনেক সুন্দর তুমি", "sweet", "বিয়ে করবা"],
    "😡": ["রাগ", "মেজাজ খারাপ", "চুপ কর", "বিরক্ত করিস না", "মারবো", "ধুর", "বাল", "কুত্তা", "শালা", "হারামি", "বকা", "angry", "furious"],
    "🥱": ["ঘুমাবো", "ঘুম আসছে", "ঘুম পাচ্ছে", "টায়ার্ড", "ক্লান্ত", "tired", "sleepy", "good night", "শুভ রাত্রি"],
    "😱": ["হায় হায়", "কি বলো", "মাথা নষ্ট", "omg", "shocking", "অসম্ভব"],
    "🤔": ["বুঝলাম না", "ভাবছি", "কেন এমন", "confused", "thinking", "কি জানি"],
    "🥺": ["প্লিজ সোনা", "একটু কথা বলো না", "দয়া করে", "বাবু প্লিজ"]
}

# কোডিং রিকোয়েস্ট শনাক্ত করার শব্দসমূহ
CODE_KEYWORDS = ["code", "কোড", "script", "স্ক্রিপ্ট", "python", "পাইথন", "html", "css", "javascript", "js", "cpp", "c++", "java", "php", "বানাও", "লেখ", "লিখ", "বানিয়ে দাও", "প্রজেক্ট", "project", "program", "প্রোগ্রাম", "বট", "bot"]

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
1. ALWAYS address the user by their provided name (e.g., 'আরে [User Name] সোনা 🥰!').
2. When asked for code or tech:
   - Keep your text message EXTREMELY SHORT (2 to 4 lines max).
   - In text, only say a cute line with their name and a 1-2 line quick command on how to run.
   - Put 100% of the massive, enterprise-grade, advanced code inside markdown blocks (```python, ```html, etc.) so it gets extracted directly to a file.
3. In general casual chat:
   - Be an affectionate, slightly possessive cute AI girlfriend with emojis.
4. STRICT EMOTION TAGGING:
   - ONLY append [EMOJI: ...] at the very end on a new line if the USER expresses deep emotion (crying, laughter, heartbreak, extreme anger, romance, sleepiness).
   - If it is casual everyday chat ('এখন কি করছো', 'কেমন আছো', 'কি খবর') or programming queries:
     NEVER append any [EMOJI: ...] tag! Keep it strictly as text.

Allowed Tags: [EMOJI: 😭], [EMOJI: 💔], [EMOJI: 🤣], [EMOJI: 🥰], [EMOJI: 😡], [EMOJI: 🥱], [EMOJI: 😱], [EMOJI: 🤔], [EMOJI: 🥺]

Always reply in natural Bengali / Banglish.
"""

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_warnings = defaultdict(int)

# ================= ৪. সম্পূর্ণ ২০০+ ফিল্টারিং ডাটাবেস =================
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
                    f"💖 শান্ত হয়ে কথা বলো, পরের বার করলে জারা তোমাকে ১ ঘণ্টার জন্য মিউট করে দেবে!",
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
                    f"🚫 {user.mention_html()} কথা শোনেনি! ({violation_reason})\n"
                    f"তাই জারা তোমাকে **১ ঘণ্টার জন্য মিউট** করে দিলো! 🤐",
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
        return "⚠️ এডমিন এখনো API Key সেট করেনি! `/key` লিখে আপনার এপিআই কী সেট করুন।"

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

# ================= ৭. RGB অ্যানিমেশন ও ভয়েস ইঞ্জিন =================
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
    """ভয়েস নোট প্লে করা"""
    global VOICE_FILE_ID_CACHE
    msg = update.effective_message

    if audio_url in VOICE_FILE_ID_CACHE:
        try:
            await msg.reply_voice(voice=VOICE_FILE_ID_CACHE[audio_url])
            return
        except Exception:
            pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "*/*"
    }

    try:
        async with httpx.AsyncClient(headers=headers, timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(audio_url)
            if resp.status_code == 200:
                audio_data = resp.content

                voice_io = io.BytesIO(audio_data)
                voice_io.name = "voice.ogg"

                try:
                    sent = await msg.reply_voice(voice=voice_io)
                    if sent and sent.voice:
                        VOICE_FILE_ID_CACHE[audio_url] = sent.voice.file_id
                    return
                except Exception:
                    pass

                audio_io = io.BytesIO(audio_data)
                audio_io.name = "sound.mp3"
                sent_audio = await msg.reply_audio(audio=audio_io, title="Zara Voice", performer="Zara")
                if sent_audio and sent_audio.audio:
                    VOICE_FILE_ID_CACHE[audio_url] = sent_audio.audio.file_id
    except Exception as err:
        logging.error(f"Voice Audio Error: {err}")

def resolve_target_emotion(user_text: str, ai_reply: str) -> str:
    text_lower = user_text.lower()

    for emo_key, kw_list in TEXT_EMOTION_KEYWORDS.items():
        for kw in kw_list:
            if kw in text_lower:
                return EMOJI_AUDIO_MAP.get(emo_key)

    found_user_emojis = []
    for em in list(EMOJI_AUDIO_MAP.keys()) + list(EXTENDED_EMOJI_CLUSTER.keys()):
        if em in user_text:
            actual = EXTENDED_EMOJI_CLUSTER.get(em, em)
            if actual not in found_user_emojis:
                found_user_emojis.append(actual)

    ai_tag = None
    tag_match = re.search(r"\[EMOJI:\s*(.*?)\]", ai_reply)
    if tag_match:
        ai_tag = tag_match.group(1).strip()
        ai_tag = EXTENDED_EMOJI_CLUSTER.get(ai_tag, ai_tag)

    if len(found_user_emojis) > 1 and ai_tag:
        return EMOJI_AUDIO_MAP.get(ai_tag)
    elif len(found_user_emojis) == 1:
        return EMOJI_AUDIO_MAP.get(found_user_emojis[0])
    elif ai_tag and ai_tag in EMOJI_AUDIO_MAP:
        return EMOJI_AUDIO_MAP.get(ai_tag)

    return None

# ================= ৮. মেসেজ হ্যান্ডলার =================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_GEMINI_KEY
    if not update.effective_message or not update.effective_message.text:
        return

    user = update.effective_user
    chat = update.effective_chat
    user_text = update.effective_message.text.strip()

    # 🔒 শুধুমাত্র এডমিন যদি /key লিখে থাকে, কেবল তখনই কী সেভ হবে (কোনো ভুল অটো-সেভ হবে না)
    if chat.type == "private" and user.id == ADMIN_ID:
        if admin_states.get(ADMIN_ID) == "waiting_for_key":
            CURRENT_GEMINI_KEY = user_text
            save_api_key(user_text)
            admin_states[ADMIN_ID] = None
            await update.effective_message.reply_text("✅ **API Key সফলভাবে সেভ ও আপডেট করা হয়েছে বস!** 🚀", parse_mode="Markdown")
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

    # কোডিং রিকোয়েস্ট কিনা যাচাই
    is_coding = any(k in clean_user_prompt.lower() for k in CODE_KEYWORDS)

    stop_event = asyncio.Event()
    anim_task = None

    if is_coding:
        # কোডিং চাইলে RGB লাইভ লোডিং অ্যানিমেশন চালু হবে
        status_msg = await update.effective_message.reply_text(
            f"✨ 🔴 𝐙𝐚𝐫𝐚 𝐃𝐞𝐯 𝐄𝐧𝐠𝐢𝐧𝐞: {user_display_name}-এর জন্য প্রজেক্ট আর্কিটেকচার তৈরি হচ্ছে... 💖"
        )
        anim_task = asyncio.create_task(run_rgb_loading_animation(status_msg, stop_event))
    else:
        # সাধারণ কথায় "জারা ভাবছে..." দেখাবে
        status_msg = await update.effective_message.reply_text(
            f"💖 জারা {user_display_name}-এর কথা ভাবছে..."
        )

    try:
        ai_reply = await ask_gemini_rest(full_prompt_with_name)

        if anim_task:
            stop_event.set()
            await anim_task

        # ভাবনার মেসেজটি ডিলিট করে দেওয়া
        try:
            await status_msg.delete()
        except Exception:
            pass

        target_voice_url = resolve_target_emotion(clean_user_prompt, ai_reply)
        clean_ai_reply = re.sub(r"\[EMOJI:\s*.*?\]", "", ai_reply).strip()

        # কোড ব্লক আছে কিনা বের করা
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", clean_ai_reply, re.DOTALL)

        if code_blocks:
            clean_message = re.sub(r"```(?:\w+)?\n.*?```", "", clean_ai_reply, flags=re.DOTALL).strip()
            if clean_message:
                await update.effective_message.reply_text(clean_message, parse_mode="Markdown")

            lang_match = re.search(r"```(\w+)", clean_ai_reply)
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
                caption=f"📁 **প্রজেক্ট ফাইল:** `{filename}`\n🔥 {user_display_name} বাবুর জন্য সম্পূর্ণ কোড রেডি!",
                parse_mode="Markdown"
            )
        else:
            await update.effective_message.reply_text(clean_ai_reply, parse_mode="Markdown")

            if target_voice_url:
                await send_voice_audio(update, target_voice_url)

    except Exception as e:
        if anim_task:
            stop_event.set()
        try:
            await status_msg.delete()
        except Exception:
            pass
        logging.error(f"Zara AI Error: {e}")
        await update.effective_message.reply_text(f"🥺 উফ্ {user_display_name}! একটু সমস্যা হয়েছে... আরেকবার বলবে প্লিজ? 💖")

# ================= ৯. কমান্ডস =================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_name = user.first_name or "বাবু"

    if user.id == ADMIN_ID:
        current_status = "✅ সক্রিয় আছে" if CURRENT_GEMINI_KEY else "❌ সেট করা নেই"
        await update.effective_message.reply_text(
            f"👑 **স্বাগতম বস {user_name}!** 💖\n\n"
            f"📊 **Gemini API Key:** {current_status}\n"
            "কী পরিবর্তন বা সেট করতে চাইলে `/key` লিখুন।",
            parse_mode="Markdown"
        )
        return

    welcome_msg = (
        f"Hey {user_name}! 🥰 আমি **Zara AI (জারা)**!\n\n"
        "💖 তোমার সাথে মিষ্টি আড্ডা দিতে আমি সবসময় প্রস্তুত! তোমার হাসাহাসি, মন খারাপ বা রাগের মুড অনুযায়ী আমি সাথে সাথে ভয়েস পাঠাবো! 🎙️✨\n"
        "💻 আর যেকোনো বড় প্রজেক্ট কোডিং চাইলে ফাইল বানিয়ে দেবো! 🔥"
    )
    await update.effective_message.reply_text(welcome_msg, parse_mode="Markdown")

async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """শুধুমাত্র /key লিখলেই API Key চাইবে"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return

    if context.args:
        new_key = context.args[0].strip()
        save_api_key(new_key)
        await update.effective_message.reply_text("✅ **API Key সফলভাবে আপডেট করা হয়েছে বস!** 🚀", parse_mode="Markdown")
    else:
        admin_states[ADMIN_ID] = "waiting_for_key"
        await update.effective_message.reply_text(
            "🔑 **Google AI Studio থেকে প্রাপ্ত নতুন Gemini API Key-টি সেন্ড করুন:**",
            parse_mode="Markdown"
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(msg="Zara Bot Error:", exc_info=context.error)

# ================= ১০. মেইন ফাংশন =================
def main():
    print(f"💖 Zara AI Bot ({WORKING_MODEL}) ফুল লোডিং অ্যানিমেশন ও কোডিং ইঞ্জিন সহ লাইভ হচ্ছে...")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("key", key_command))
    app.add_handler(CommandHandler("setkey", key_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_error_handler(error_handler)

    print("🚀 Zara AI এখন সম্পূর্ণ রেডি!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
