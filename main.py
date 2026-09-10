import asyncio
import re
import random
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions, ReactionTypeEmoji
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler
from telegram.error import TelegramError

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8768727708:AAF62zTgGvjX5TrYQJsR8X1zGZ3yMwuZrMY"  # আপনার বটের টোকেন এখানে দিন
BOT_USERNAME = "Boo0ooo_bot"   # @ বাদে আপনার বটের ইউজারনেম

# মেম্বারদের ওয়ার্নিং ট্র্যাক করার ডিকশনারি
# Structure: {chat_id: {user_id: count}}
user_warnings = {}

# সাধারণ মেসেজে রিঅ্যাকশন দেওয়ার জন্য ইমোজি লিস্ট
REACTION_EMOJIS = ["❤️", "🔥", "👍", "👏", "🎉", "🤩", "⚡", "💯", "👌"]

# ==================== ১০০+ গালি ও নিষিদ্ধ শব্দ ====================
BANNED_WORDS = [
    # বাংলা ও বাংলিশ গালি
    "maderchod", "mc", "bc", "bhodaimoda", "chudmarani", "khankir pola", "khanki", 
    "magir pola", "shala", "shali", "gandu", "bainchod", "harami", "bal", "chuda", 
    "chudani", "bogachoda", "kutta", "kuttar bacha", "podmarani", "chod", "behaiya",
    "bessha", "randi", "randir pola", "madarchod", "suor", "suorer bacha", "banchod",
    "fokirni", "khankir chele", "bokachoda", "lund", "bur", "bura", "chudis", "chudbo",
    "চুদা", "চোদ", "মাদারচোদ", "খানকি", "খানকির পোলা", "মাগীর পোলা", "শুয়োরের বাচ্চা", 
    "কুত্তার বাচ্চা", "বেশ্যা", "বাল", "বোকাচোদা", "গাঞ্জাখোর", "হারামি", "ভোদাই", 
    "ভোদাইমোদা", "লুচ্চা", "লুচ্চামি", "চুদমারানি", "রাঁড়ি", "পোদ", "লেবড়া",

    # ইংরেজি গালি
    "fuck", "fucker", "fucking", "bitch", "bastard", "asshole", "dick", "pussy", 
    "cunt", "motherfucker", "slut", "whore", "nigger", "cock", "bullshit", "prick", 
    "retard", "fag", "faggot", "scumbag", "blowjob", "dumbass",

    # স্প্যাম ও ইনবক্স সম্পর্কিত নিষিদ্ধ কথা (Bangla & English)
    "inbox asho", "inbox koro", "inbox a aso", "inbox aisho", "inbox korun", 
    "dm me", "dm koro", "come inbox", "inbox er moddhe asho", "massage dao",
    "personal a asho", "like sell", "follower sell", "id sell", "page sell",
    "sub sell", "watch time sell", "coin sell", "dollar sell", "tk lagbe",
    "free taka", "free recharge", "taka income korun", "taka income koro",
    "লাইক সেল", "আইডি সেল", "ইনবক্সে আসো", "ইনবক্স কর", "ডিএম করো", "ফলোয়ার সেল"
]

# লিংক খোঁজার জন্য রেগুলার এক্সপ্রেশন
URL_PATTERN = re.compile(
    r'(https?://[^\s]+)|(www\.[^\s]+)|(t\.me/[^\s]+)|(telegram\.me/[^\s]+)', 
    re.IGNORECASE
)

# ==================== হেল্পার ফাংশনসমূহ ====================

async def is_admin(chat, user_id: int) -> bool:
    """ইউজার অ্যাডমিন বা গ্রুপের মালিক কি না চেক করে"""
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False

def get_warning_box(user_mention: str, reason: str, warn_count: int) -> str:
    """১ম সতর্কবার্তার ডিজাইন বক্স"""
    return (
        "╔═══════════════════════════════╗\n"
        "║      ⚠️ **গ্রুপ সতর্কবার্তা (WARNING)** ⚠️\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 **ব্যবহারকারী:** {user_mention}\n"
        f"║ 🚫 **কারণ:** {reason}\n"
        f"║ ⚠️ **ওয়ার্নিং সংখ্যা:** [{warn_count}/2]\n"
        "╠═══════════════════════════════╣\n"
        "║ 📢 **সতর্কতা:** গ্রুপের নিয়ম মেনে চলুন।\n"
        "║ ২য় বার ভুল করলে **১ ঘণ্টার জন্য মিউট**\n"
        "║ করা হবে!\n"
        "╚═══════════════════════════════╝"
    )

def get_mute_box(user_mention: str, reason: str) -> str:
    """মিউট করার সময় ডিজাইন বক্স"""
    return (
        "╔═══════════════════════════════╗\n"
        "║        🔇 **শাস্তিমূলক ব্যবস্থা (MUTED)** 🔇\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 **ব্যবহারকারী:** {user_mention}\n"
        f"║ 🚫 **কারণ:** {reason} (পুনরাবৃত্তি)\n"
        "║ ⏳ **শাস্তি:** ১ ঘণ্টার জন্য মিউট!\n"
        "╠═══════════════════════════════╣\n"
        "║ 💡 ১ ঘণ্টা পর আপনি স্বয়ংক্রিয়ভাবে কথা\n"
        "║ বলার সুযোগ পাবেন। গ্রুপ শান্ত রাখুন।\n"
        "╚═══════════════════════════════╝"
    )

def get_unmute_box(user_mention: str) -> str:
    """আনমিউট নোটিশের ডিজাইন বক্স"""
    return (
        "╔═══════════════════════════════╗\n"
        "║        🔊 **আনমিউট নোটিফিকেশন** 🔊\n"
        "╠═══════════════════════════════╣\n"
        f"║ 👤 **ব্যবহারকারী:** {user_mention}\n"
        "║ ✅ **অবস্থা:** আপনাকে আনমিউট করা হলো।\n"
        "╠═══════════════════════════════╣\n"
        "║ দয়া করে গ্রুপের নিয়ম মেনে চলুন এবং সুন্দর\n"
        "║ পরিবেশ বজায় রাখুন। শুভ আড্ডা!\n"
        "╚═══════════════════════════════╝"
    )

async def auto_unmute_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, user_mention: str):
    """১ ঘণ্টা অপেক্ষা করে ইউজারকে আনমিউট করার টাস্ক"""
    await asyncio.sleep(3600)  # ৩৬০০ সেকেন্ড = ১ ঘণ্টা
    try:
        # সকল মেসেজ পারমিশন ফিরিয়ে দেওয়া
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await context.bot.restrict_chat_member(chat_id=chat_id, user_id=user_id, permissions=permissions)
        
        # ওয়ার্নিং কাউন্ট রিসেট করা
        if chat_id in user_warnings and user_id in user_warnings[chat_id]:
            user_warnings[chat_id][user_id] = 0

        # সুন্দর আনমিউট বক্স সেন্ড করা
        await context.bot.send_message(
            chat_id=chat_id,
            text=get_unmute_box(user_mention),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Error while unmuting: {e}")

# ==================== মূল ফিল্টারিং হ্যান্ডলার ====================

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    # প্রাইভেট চ্যাটে কাজ করবে না, শুধু গ্রুপে কাজ করবে
    if not message or not chat or chat.type in ["private", "channel"]:
        return

    # সিস্টেম মেসেজ বা বট নিজে মেসেজ পাঠালে ইগনোর করবে
    if not user or user.is_bot:
        return

    # ইউজার অ্যাডমিন কি না যাচাই
    admin_status = await is_admin(chat, user.id)
    if admin_status:
        return  # অ্যাডমিনদের কোনো রেস্ট্রিকশন নেই

    text = message.text or message.caption or ""
    lower_text = text.lower()
    user_mention = f"[{user.first_name}](tg://user?id={user.id})"
    chat_id = chat.id
    user_id = user.id

    violation_reason = None

    # ১. ফরওয়ার্ড মেসেজ চেক
    if message.forward_date or message.forward_from or message.forward_from_chat:
        violation_reason = "ফরওয়ার্ড মেসেজ পাঠানো সম্পূর্ণ নিষিদ্ধ"

    # ২. লিংক প্রোটেকশন চেক
    elif URL_PATTERN.search(text):
        violation_reason = "গ্রুপে যেকোনো ধরনের লিংক শেয়ার করা নিষিদ্ধ"

    # ৩. গালি ও স্প্যাম টেক্সট ফিল্টার
    elif any(bad_word in lower_text for bad_word in BANNED_WORDS):
        violation_reason = "অশালীন ভাষা / স্প্যামিং / ইনবক্স ডাকার নিষেধাজ্ঞা ভঙ্গ"

    # ৪. বড় মেসেজ (৪০০ অক্ষরের বেশি) প্রোটেকশন
    elif len(text) > 400:
        violation_reason = "গ্রুপে অতিরিক্ত বড় টেক্সট/স্প্যামিং করা নিষিদ্ধ"

    # ৫. অন্য কোনো বট বা প্রোফাইল মেনশন ফিল্টার
    elif message.entities:
        for entity in message.entities:
            if entity.type == "mention":
                mention_text = text[entity.offset:entity.offset + entity.length].replace("@", "")
                # বটের নিজস্ব নাম ব্যতীত অন্য কোনো মেনশন ব্লক করা
                if mention_text.lower() != BOT_USERNAME.lower():
                    violation_reason = "অন্যান্য বট বা প্রোফাইল মেনশন করা নিষিদ্ধ"
                    break

    # ==================== শাস্তি কার্যকর করার অংশ ====================
    if violation_reason:
        try:
            # সাথে সাথে অবৈধ মেসেজ ডিলিট
            await message.delete()
        except TelegramError:
            pass

        # ইউজার ওয়ার্নিং ট্র্যাক করা
        if chat_id not in user_warnings:
            user_warnings[chat_id] = {}
        user_warnings[chat_id][user_id] = user_warnings[chat_id].get(user_id, 0) + 1

        warn_count = user_warnings[chat_id][user_id]

        if warn_count == 1:
            # ১ম বার ওয়ার্নিং বক্স
            warn_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=get_warning_box(user_mention, violation_reason, 1),
                parse_mode=ParseMode.MARKDOWN
            )
            # ২০ সেকেন্ড পর ওয়ার্নিং মেসেজ ডিলিট করতে চাইলে আনকমেন্ট করতে পারেন
            # await asyncio.sleep(20); await warn_msg.delete()

        elif warn_count >= 2:
            # ২য় বার মিউট (১ ঘণ্টার জন্য)
            try:
                mute_permissions = ChatPermissions(can_send_messages=False)
                await context.bot.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    permissions=mute_permissions,
                    until_date=datetime.now() + timedelta(hours=1)
                )

                await context.bot.send_message(
                    chat_id=chat_id,
                    text=get_mute_box(user_mention, violation_reason),
                    parse_mode=ParseMode.MARKDOWN
                )

                # ১ ঘণ্টার পর স্বয়ংক্রিয়ভাবে আনমিউট করার টাস্ক চালু করা
                asyncio.create_task(auto_unmute_task(context, chat_id, user_id, user_mention))

            except TelegramError as e:
                print(f"Error restricting user: {e}")

        return

    # ==================== সাধারণ মেসেজে অটো রিঅ্যাকশন ====================
    try:
        chosen_emoji = random.choice(REACTION_EMOJIS)
        await message.set_reaction(reaction=[ReactionTypeEmoji(emoji=chosen_emoji)])
    except Exception:
        pass  # কোনো গ্রুপে রিঅ্যাকশন পারমিশন অফ থাকলে এরর এড়িয়ে যাবে

# ==================== মেইন রানার ====================
def main():
    print("বট সফলভাবে চালু হয়েছে...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # মেসেজ ফিল্টার হ্যান্ডলার যুক্ত করা
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_group_messages))

    # বট পোলিং শুরু
    app.run_polling()

if __name__ == "__main__":
    main()
