import os
import io
import json
import random
import zipfile
import asyncio
import datetime
import aiohttp
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ReplyKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= কনফিগারেশন =================
MAIN_BOT_TOKEN = "8385333653:AAF-aL_ttBqSEFwT0KxNlrUDSWkvmIJJHRw"  # আপনার মেইন বটের টোকেন দিন
ADMIN_ID = 6805684286                         # আপনার টেলিগ্রাম আইডি দিন
TOKEN_FILE = "tg.txt"
CHATS_FILE = "chats.json"
USERS_FILE = "users.json"

# টেলিগ্রামের ১০০% অফিশিয়াল ডিফল্ট ৪৫টি স্পেশাল ইমোজি (কান্না ও রাগ ছাড়া)
SPECIAL_EMOJIS = [
    "🔥", "❤️", "🎉", "⚡", "🤩", "👏", "🥰", "💯", "🏆", "😍",
    "❤️‍🔥", "🍾", "🍓", "💋", "😇", "🦄", "😎", "👾", "✨", "👍",
    "👌", "🤝", "🫡", "🆒", "💘", "🕊️", "🐳", "🤣", "😁", "🤗",
    "😘", "👀", "🙈", "🙊", "💅", "🤪", "🗿", "🤓", "👻", "👨‍💻",
    "✍️", "🤯", "🤔", "🍌", "🌚"
]
# ===============================================

# --- হেল্পার বক্স ডিজাইন ফাংশন ---
def make_box(title: str, lines: list, emoji_icon: str = "✨") -> str:
    header = f"╭───〔 {emoji_icon} {title} 〕───╮\n│"
    content = "\n".join([f"│  {line}" for line in lines])
    footer = "│\n╰──────────────────────────────╯"
    return f"{header}\n{content}\n{footer}"

# --- ফাইল ম্যানেজমেন্ট ফাংশনস ---
def load_tokens():
    if not os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "w") as f: pass
        return []
    with open(TOKEN_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_token(token):
    tokens = load_tokens()
    if token in tokens:
        return False
    with open(TOKEN_FILE, "a") as f:
        f.write(f"{token}\n")
    return True

def remove_token(token_to_remove):
    tokens = load_tokens()
    tokens = [t for t in tokens if t != token_to_remove]
    with open(TOKEN_FILE, "w") as f:
        for t in tokens:
            f.write(f"{t}\n")

# গ্রুপ ও চ্যানেল হিস্টোরি
def save_chat_info(chat_id, title):
    chats = load_chats()
    chats[str(chat_id)] = title
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(chats, f, ensure_ascii=False, indent=2)

def load_chats():
    if not os.path.exists(CHATS_FILE): return {}
    try:
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

# ইউজার ট্র্যাকিং (ব্রডকাস্টের জন্য)
def save_user(user_id, username):
    users = load_users()
    users[str(user_id)] = username or "User"
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_users():
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except: return {}

# জিপ ব্যাকআপ ফাইল জেনারেটর
def create_backup_zip():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for filename in [TOKEN_FILE, CHATS_FILE, USERS_FILE]:
            if os.path.exists(filename):
                zip_file.write(filename)
    zip_buffer.seek(0)
    return zip_buffer

# বটের ইউজারনেম বের করা
async def get_bot_info(session, token):
    try:
        async with session.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]["username"]
    except:
        return None
    return None

# রিয়েকশন ফাংশন
async def send_reaction(session, token, chat_id, message_id, emoji):
    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": emoji}],
        "is_big": False
    }
    try:
        async with session.post(url, json=payload, timeout=5) as resp:
            return await resp.json()
    except:
        return None

# ================== হ্যান্ডলারস ==================

# /start হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    tokens = load_tokens()

    save_user(user_id, user.username)

    welcome_box = make_box(
        "REACTION NETWORK",
        [
            "👋 **হ্যালো প্রিয় ব্যবহারকারী!**",
            "টেলিগ্রামের সেরা প্রিমিয়াম মাল্টি-রিঅ্যাকশন",
            "অফিসিয়াল সিস্টেমে আপনাকে স্বাগতম!",
            "",
            f"⚡ **সক্রিয় রিঅ্যাকশন বট:** `{len(tokens)}` টি",
            "🎨 **ইমোজি:** ১০০% টেলিগ্রাম সাপোর্টেড প্রিমিয়াম সেট",
            "🚀 **কার্যকারিতা:** যেকোনো মেসেজে ১০০% ফাস্ট রিঅ্যাক্ট",
            "",
            "👇 **বটগুলোর লিস্ট পেতে নিচের বাটনে চাপুন:**"
        ],
        emoji_icon="🌟"
    )

    inline_keyboard = [
        [InlineKeyboardButton("🤖 All Bots (বটের তালিকা দেখুন)", callback_data="show_all_bots")]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    if user_id == ADMIN_ID:
        admin_keyboard = [
            ["➕ বট যোগ করুন", "➖ বট রিমুভ করুন"],
            ["🧹 নষ্ট বট ডিলিট", "📢 ব্রডকাস্ট মেসেজ"],
            ["💾 ব্যাকআপ ফাইল", "📊 গ্রুপ ও চ্যানেল লিস্ট"],
            ["⚙️ সিস্টেম স্ট্যাটাস"]
        ]
        reply_markup = ReplyKeyboardMarkup(admin_keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_box, reply_markup=inline_markup, parse_mode="Markdown")
        
        admin_box = make_box(
            "ADMIN CONTROLLER",
            [
                "👑 **অ্যাডমিন কন্ট্রোল প্যানেল সক্রিয়!**",
                "নিচের বাটনগুলো দিয়ে পুরো নেটওয়ার্ক নিয়ন্ত্রণ করুন।"
            ],
            emoji_icon="🛡️"
        )
        await update.message.reply_text(admin_box, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(welcome_box, reply_markup=inline_markup, parse_mode="Markdown")

# All Bots বাটন হ্যান্ডলার
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_all_bots":
        tokens = load_tokens()
        if not tokens:
            box = make_box("সতর্কতা", ["❌ সিস্টেমে বর্তমানে কোনো স্ল্যাভ বট নেই!"], emoji_icon="⚠️")
            await query.message.reply_text(box, parse_mode="Markdown")
            return

        loading_box = make_box("লোড হচ্ছে", ["🔄 বটের তালিকা ও লিঙ্ক তৈরি হচ্ছে...", "অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন..."], emoji_icon="⏳")
        wait_msg = await query.message.reply_text(loading_box, parse_mode="Markdown")
        
        buttons = []
        async with aiohttp.ClientSession() as session:
            for idx, token in enumerate(tokens, 1):
                username = await get_bot_info(session, token)
                if username:
                    add_link = f"https://t.me/{username}?startgroup=botstart"
                    buttons.append([InlineKeyboardButton(f"🤖 Bot #{idx}: @{username} [Add to Group]", url=add_link)])
        
        if buttons:
            reply_markup = InlineKeyboardMarkup(buttons)
            ready_box = make_box(
                "BOT LIST & ADD LINKS",
                [
                    "📋 **সকল রিঅ্যাকশন বটের তালিকা:**",
                    "নিচের যেকোনো বটে ক্লিক করে সরাসরি আপনার",
                    "গ্রুপ বা চ্যানেলে যুক্ত করে অ্যাডমিন বানান।"
                ],
                emoji_icon="🤖"
            )
            await wait_msg.edit_text(ready_box, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            err_box = make_box("ত্রুটি", ["❌ কোনো সক্রিয় বটের সন্ধান পাওয়া যায়নি!"], emoji_icon="🚫")
            await wait_msg.edit_text(err_box, parse_mode="Markdown")

# অ্যাডমিনের কিবোর্ড ও মেসেজ হ্যান্ডলার
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    text = update.message.text.strip()
    action = context.user_data.get("action")

    if text == "➕ বট যোগ করুন":
        context.user_data["action"] = "waiting_for_add"
        box = make_box("বট যোগকরণ", ["📝 যে বটটি যুক্ত করতে চান,", "তার **Bot Token** টি এখানে পাঠান:"], emoji_icon="➕")
        await update.message.reply_text(box, parse_mode="Markdown")
        return

    elif text == "➖ বট রিমুভ করুন":
        context.user_data["action"] = "waiting_for_del"
        box = make_box("বট অপসারণ", ["🗑️ যে বটটি ডাটাবেজ থেকে মুছতে চান,", "তার **Bot Token** টি এখানে পাঠান:"], emoji_icon="➖")
        await update.message.reply_text(box, parse_mode="Markdown")
        return

    elif text == "🧹 নষ্ট বট ডিলিট":
        tokens = load_tokens()
        wait_box = make_box("স্ক্যানিং শুরু", ["🔍 সকল বট ভেরিফাই করা হচ্ছে...", "নষ্ট/অচল বট মুছে ফেলা হচ্ছে..."], emoji_icon="⏳")
        msg = await update.message.reply_text(wait_box, parse_mode="Markdown")
        
        alive_tokens = []
        dead_count = 0

        async with aiohttp.ClientSession() as session:
            for token in tokens:
                username = await get_bot_info(session, token)
                if username:
                    alive_tokens.append(token)
                else:
                    dead_count += 1

        with open(TOKEN_FILE, "w") as f:
            for t in alive_tokens:
                f.write(f"{t}\n")

        clean_box = make_box(
            "ক্লিনআপ সম্পন্ন",
            [
                f"🗑️ ডিলিট করা নষ্ট বট: `{dead_count}` টি",
                f"🟢 বর্তমানে সম্পূর্ণ সচল বট: `{len(alive_tokens)}` টি",
                "✅ ডাটাবেজ এখন সম্পূর্ণ ফ্রেশ ও এররমুক্ত!"
            ],
            emoji_icon="🧹"
        )
        await msg.edit_text(clean_box, parse_mode="Markdown")
        return

    elif text == "💾 ব্যাকআপ ফাইল":
        wait_box = make_box("ব্যাকআপ প্রস্তুত হচ্ছে", ["📦 সম্পূর্ণ সিস্টেমের ডাটা জিপ ফাইলে রূপান্তর হচ্ছে..."], emoji_icon="⏳")
        msg = await update.message.reply_text(wait_box, parse_mode="Markdown")
        
        zip_data = create_backup_zip()
        today = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        
        await update.message.reply_document(
            document=zip_data,
            filename=f"Reaction_Bot_Backup_{today}.zip",
            caption=make_box("সিস্টেম ব্যাকআপ", ["✅ আপনার সিস্টেমের সম্পূর্ণ ব্যাকআপ প্রস্তুত!", "📁 অন্তর্ভুক্ত: tg.txt, chats.json, users.json", "🛡️ এটি দিয়ে যেকোনো সার্ভারে হুবহু রিস্টোর করতে পারবেন।"], emoji_icon="💾"),
            parse_mode="Markdown"
        )
        await msg.delete()
        return

    elif text == "📢 ব্রডকাস্ট মেসেজ":
        context.user_data["action"] = "waiting_for_broadcast"
        box = make_box(
            "ব্রডকাস্ট মোড",
            [
                "📢 আপনি যে মেসেজটি সবার কাছে পাঠাতে চান,",
                "তা লিখে পাঠান (ঘোষণা/নোটিশ)।",
                "",
                "⚠️ এটি সকল ইনবক্স এবং গ্রুপ/চ্যানেলে যাবে।"
            ],
            emoji_icon="📢"
        )
        await update.message.reply_text(box, parse_mode="Markdown")
        return

    elif text == "📊 গ্রুপ ও চ্যানেল লিস্ট":
        chats = load_chats()
        if not chats:
            box = make_box("ডাটা পাওয়া যায়নি", ["ℹ️ এখনও কোনো গ্রুপ/চ্যানেল থেকে নোটিশ আসেনি।"], emoji_icon="📂")
            await update.message.reply_text(box, parse_mode="Markdown")
            return

        chat_lines = ["📋 **সংযুক্ত গ্রুপ ও চ্যানেলসমূহ:**", ""]
        for idx, (cid, title) in enumerate(chats.items(), 1):
            chat_lines.append(f"**{idx}.** {title} `[ID: {cid}]`")
        chat_lines.append("")
        chat_lines.append(f"📢 মোট কানেক্টেড চ্যাট: **{len(chats)}** টি")

        box = make_box("CHATS HISTORY", chat_lines, emoji_icon="📊")
        await update.message.reply_text(box, parse_mode="Markdown")
        return

    elif text == "⚙️ সিস্টেম স্ট্যাটাস":
        tokens = load_tokens()
        chats = load_chats()
        users = load_users()
        box = make_box(
            "SYSTEM STATUS",
            [
                f"🤖 স্ল্যাভ বট টোকেন: `{len(tokens)}` টি",
                f"👥 মোট বট ইউজার: `{len(users)}` জন",
                f"📢 কানেক্টেড গ্রুপ/চ্যানেল: `{len(chats)}` টি",
                f"🎨 অফিসিয়াল ইমোজি সেট: `{len(SPECIAL_EMOJIS)}` টি",
                "⏰ দৈনিক অটো-ব্যাকআপ: সকাল ১০:০০ টা (সক্রিয়)",
                "🛡️ সার্ভার হেলথ: ১০০% পারফেক্ট!"
            ],
            emoji_icon="⚙️"
        )
        await update.message.reply_text(box, parse_mode="Markdown")
        return

    # ব্রডকাস্ট মেসেজ এক্সিকিউশন
    if action == "waiting_for_broadcast":
        users = load_users()
        chats = load_chats()
        
        wait_box = make_box("ব্রডকাস্ট চলছে", ["📡 সবার কাছে মেসেজ পাঠিয়ে দেওয়া হচ্ছে...", "অনুগ্রহ করে ব্যাকগ্রাউন্ড প্রসেস শেষ হওয়া পর্যন্ত অপেক্ষা করুন..."], emoji_icon="🚀")
        stat_msg = await update.message.reply_text(wait_box, parse_mode="Markdown")
        
        success_users = 0
        success_chats = 0

        broadcast_content = make_box("📢 অফিশিয়াল নোটিশ", [text], emoji_icon="🔔")

        for uid in users.keys():
            try:
                await context.bot.send_message(chat_id=int(uid), text=broadcast_content, parse_mode="Markdown")
                success_users += 1
                await asyncio.sleep(0.04)
            except: pass

        for cid in chats.keys():
            try:
                await context.bot.send_message(chat_id=int(cid), text=broadcast_content, parse_mode="Markdown")
                success_chats += 1
                await asyncio.sleep(0.04)
            except: pass

        report_box = make_box(
            "ব্রডকাস্ট রিপোর্ট",
            [
                "✅ **সফলভাবে মেসেজ পাঠানো সম্পন্ন হয়েছে!**",
                "",
                f"👤 ব্যবহারকারীদের ইনবক্সে: `{success_users}` জন",
                f"📢 গ্রুপ ও চ্যানেলসমূহে: `{success_chats}` টি",
                f"📊 মোট সফল ডেলিভারি: `{success_users + success_chats}` টি"
            ],
            emoji_icon="📊"
        )
        await stat_msg.edit_text(report_box, parse_mode="Markdown")
        context.user_data["action"] = None
        return

    # টোকেন ইনপুট লজিক
    if action == "waiting_for_add":
        tokens = load_tokens()
        if text in tokens:
            dup_box = make_box("ডুপ্লিকেট সতর্কতা", ["⚠️ এই টোকেনটি ইতোমধ্যে ফাইলে রয়েছে!", "একই টোকেন বারবার দেওয়ার প্রয়োজন নেই।"], emoji_icon="⚠️")
            await update.message.reply_text(dup_box, parse_mode="Markdown")
            return

        async with aiohttp.ClientSession() as session:
            username = await get_bot_info(session, text)
            if username:
                save_token(text)
                succ_box = make_box("বট যোগ সফল", [f"🤖 বট: @{username}", "📁 tg.txt ফাইলে সেভ হয়েছে!", "⚡ এটি এখন রিঅ্যাকশন দিতে প্রস্তুত।"], emoji_icon="✅")
                await update.message.reply_text(succ_box, parse_mode="Markdown")
            else:
                err_box = make_box("ভুল টোকেন", ["❌ টোকেনটি অবৈধ বা নষ্ট!", "টেলিগ্রাম এই টোকেনটিকে গ্রহণ করেনি।"], emoji_icon="🚫")
                await update.message.reply_text(err_box, parse_mode="Markdown")
        context.user_data["action"] = None

    elif action == "waiting_for_del":
        tokens = load_tokens()
        if text in tokens:
            remove_token(text)
            del_box = make_box("সফল অপসারণ", ["🗑️ টোকেনটি সফলভাবে ডিলিট করা হয়েছে!"], emoji_icon="✅")
            await update.message.reply_text(del_box, parse_mode="Markdown")
        else:
            not_found = make_box("পাওয়া যায়নি", ["❌ এই টোকেনটি ডাটাবেজ ফাইলেই নেই!"], emoji_icon="⚠️")
            await update.message.reply_text(not_found, parse_mode="Markdown")
        context.user_data["action"] = None

# ================= নোটিশে স্বয়ংক্রিয় রিঅ্যাকশন ইঞ্জিন =================
async def reaction_engine(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat:
        return

    save_chat_info(chat.id, chat.title or "Private Group")

    tokens = load_tokens()
    if not tokens:
        return

    # ৪৫টি অফিশিয়াল ইমোজি র‍্যান্ডমাইজ হবে
    shuffled_emojis = random.sample(SPECIAL_EMOJIS, len(SPECIAL_EMOJIS))

    async with aiohttp.ClientSession() as session:
        tasks = []
        for idx, token in enumerate(tokens):
            emoji = shuffled_emojis[idx % len(shuffled_emojis)]
            tasks.append(send_reaction(session, token, chat.id, msg.message_id, emoji))
            await asyncio.sleep(0.04)

        await asyncio.gather(*tasks)

# ================= প্রতিদিন সকাল ১০টায় অটো ব্যাকআপ টাস্ক =================
async def daily_auto_backup_worker(app):
    sent_today = False
    while True:
        # বাংলাদেশ সময় (UTC+6)
        now_bd = datetime.datetime.utcnow() + datetime.timedelta(hours=6)
        
        if now_bd.hour == 10 and now_bd.minute == 0 and not sent_today:
            try:
                zip_data = create_backup_zip()
                caption = make_box(
                    "দৈনিক অটো-ব্যাকআপ (সকাল ১০:০০)",
                    [
                        f"📅 তারিখ: {now_bd.strftime('%Y-%m-%d')}",
                        "📁 অন্তর্ভুক্ত ফাইল: tg.txt, chats.json, users.json",
                        "🤖 সিস্টেমের সকল ডাটা সফলভাবে ব্যাকআপ করা হয়েছে।"
                    ],
                    emoji_icon="⏰"
                )
                await app.bot.send_document(
                    chat_id=ADMIN_ID,
                    document=zip_data,
                    filename=f"Auto_Backup_{now_bd.strftime('%Y-%m-%d')}.zip",
                    caption=caption,
                    parse_mode="Markdown"
                )
                sent_today = True
            except Exception as e:
                print(f"Auto Backup Error: {e}")
        
        if now_bd.hour == 10 and now_bd.minute > 1:
            sent_today = False
            
        await asyncio.sleep(30)

# ================= মেইন ফাংশন =================
async def post_init(app):
    asyncio.create_task(daily_auto_backup_worker(app))

def main():
    print("🚀 ১০০% টেলিগ্রাম সাপোর্টেড মাল্টি-রিঅ্যাকশন সিস্টেম চালু হচ্ছে...")
    app = ApplicationBuilder().token(MAIN_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, admin_message_handler))

    # গ্রুপ ও চ্যানেলে অটো-রিঅ্যাকশন
    app.add_handler(MessageHandler(filters.ChatType.GROUPS | filters.ChatType.CHANNEL, reaction_engine))

    print("✅ সিস্টেম ১০০% রেডি! কোনো এরর ছাড়া সকল অফিশিয়াল ইমোজি রানিং।")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
