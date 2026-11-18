import re
import asyncio
import os
import threading
from collections import defaultdict
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ── Config ──────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN") 
BOT_NAME = "Hadi Hi2 Decorater Bot"
EMOJIS = "❤️‍🔥🎀"
DEVELOPER = "@hacked_by_hadi"
DELAY_SECONDS = 3

# 🔥 FORCE JOIN SETTING (Aapka Channel)
FORCE_JOIN_CHANNEL = "@h4cked_by_h4di" 
CHANNEL_URL = "https://t.me/h4cked_by_h4di"

# ── Storage ─────────────────────────────────────────────
user_emails = defaultdict(list)
user_seen = defaultdict(set)
pending_tasks = {}
waiting_msgs = {}

EMAIL_REGEX = re.compile(r"[\w.+-]+@(?:hi2|telegmail)\.[A-Za-z]{2,}", re.IGNORECASE)

def extract_emails(text: str):
    return EMAIL_REGEX.findall(text)

def counts(emails):
    hi2 = sum(1 for e in emails if "@hi2." in e.lower())
    tele = sum(1 for e in emails if "@telegmail." in e.lower())
    return len(emails), hi2, tele

# ── Force Join Check ────────────────────────────────────
async def is_user_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=FORCE_JOIN_CHANNEL, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception:
        return False

async def send_force_join_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL)],
        [InlineKeyboardButton("✅ Try Again", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        f"⚠️ <b>Access Denied!</b>\n\n"
        f"Bot ko use karne ke liye pehle aapko hamara channel join karna hoga.\n"
        f"Neeche diye gaye button se channel join karein, phir <b>Try Again</b> par click karein."
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

# ── Delayed Combiner ────────────────────────────────────
async def send_combined(context, chat_id, user_id):
    try:
        await asyncio.sleep(DELAY_SECONDS)
    except asyncio.CancelledError:
        return

    emails = user_emails.pop(user_id, [])
    user_seen.pop(user_id, None)
    pending_tasks.pop(user_id, None)
    wait_msg = waiting_msgs.pop(user_id, None)

    if not emails:
        return

    total, hi2, tele = counts(emails)
    combined = "\n".join(emails)

    reply = (
        f"{EMOJIS} <b>Decorated Emails</b> {EMOJIS}\n\n"
        f"<code>{combined}</code>\n\n"
        f"📊 Total: <b>{total}</b> emails (Hi2: <b>{hi2}</b>, Telegmail: <b>{tele}</b>)\n\n"
        f"👨‍💻 Developer: {DEVELOPER}"
    )

    if wait_msg:
        try:
            await wait_msg.edit_text(reply, parse_mode="HTML")
            return
        except Exception:
            pass

    await context.bot.send_message(chat_id=chat_id, text=reply, parse_mode="HTML")

# ── Start Command (With Force Join & Start Button) ──────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    # Force Join Check
    joined = await is_user_joined(user_id, context)
    if not joined:
        await send_force_join_msg(update, context)
        return

    # Agar join hai, toh Start Button show karo
    name_text = f"@{username}" if username else first_name
    keyboard = [[InlineKeyboardButton(f"🚀 Start {name_text}", callback_data="main_start")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{EMOJIS} <b>Welcome {first_name}!</b> {EMOJIS}\n\n"
        f"Bot ko start karne ke liye neeche diye gaye button par click karein.",
        parse_mode="HTML",
        reply_markup=reply_markup
    )

# ── Callback Handler (Start, Try Again, Developer) ──────
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "check_join":
        joined = await is_user_joined(user_id, context)
        if not joined:
            await query.answer("❌ Aapne abhi tak channel join nahi kiya hai!", show_alert=True)
            return
        
        # Agar join kar liya hai
        await query.answer("✅ Channel joined! Ab aap bot start kar sakte hain.", show_alert=True)
        await query.message.delete()
        
        first_name = query.from_user.first_name
        username = query.from_user.username
        name_text = f"@{username}" if username else first_name
        keyboard = [[InlineKeyboardButton(f"🚀 Start {name_text}", callback_data="main_start")]]
        
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"{EMOJIS} <b>Welcome {first_name}!</b> {EMOJIS}\n\nBot ko start karne ke liye neeche diye gaye button par click karein.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "main_start":
        await query.answer("✅ Bot Started Successfully!", show_alert=False)
        
        start_text = (
            "╔══════════════════════════╗\n"
            "   ❤️‍🔥 <b>Hadi Hi2 Decorater Bot</b> 🎀\n"
            "╚══════════════════════════╝\n\n"
            "🔥 <b>Yeh Bot kaise kaam karta hai?</b>\n"
            "🎯 Aapka jo bhi Hit message hai (jisme emails hain), use yahan bhejo.\n"
            "⚡ Main saare extra text hata kar aapko saare <b>Hi2 / Telegmail</b> emails <b>Line by Line</b> turant nikal dunga!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"👨‍💻 <b>Developer</b> : {DEVELOPER}\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ <i>Note: Duplicate emails automatic remove ho jayengi.</i>"
        )
        keyboard = [[InlineKeyboardButton("👨‍💻 Developer", callback_data="open_developer")]]
        await query.message.edit_text(start_text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "open_developer":
        await query.answer(url=f"https://t.me/{DEVELOPER.replace('@', '')}", show_alert=False)
        await query.message.reply_text(
            f"👨‍💻 <b>Developer:</b> {DEVELOPER}\n\nAap is ID par click karke direct message kar sakte hain.",
            parse_mode="HTML"
        )

# ── Clear Command ───────────────────────────────────────
async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_emails.pop(user_id, None)
    user_seen.pop(user_id, None)
    if user_id in pending_tasks:
        pending_tasks[user_id].cancel()
        pending_tasks.pop(user_id, None)
    if user_id in waiting_msgs:
        try:
            await waiting_msgs[user_id].delete()
        except Exception:
            pass
        waiting_msgs.pop(user_id, None)
    await update.message.reply_text(f"✅ Cleared. Ab naye emails bhejein {EMOJIS}")

# ── Message Handler ─────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check Force Join before processing messages
    joined = await is_user_joined(user_id, context)
    if not joined:
        await send_force_join_msg(update, context)
        return

    chat_id = update.effective_chat.id
    text = update.message.text or ""

    found = extract_emails(text)
    if not found:
        return

    new_added = 0
    for e in found:
        key = e.lower()
        if key not in user_seen[user_id]:
            user_seen[user_id].add(key)
            user_emails[user_id].append(e)
            new_added += 1

    if new_added == 0 and user_id not in waiting_msgs:
        await update.message.reply_text(
            f"⚠️ Ye emails pehle se list me hain (duplicate).\n"
            f"🧹 /clear se clear karein ya naye emails bhejein."
        )
        return

    if user_id in pending_tasks:
        pending_tasks[user_id].cancel()

    total, hi2, tele = counts(user_emails[user_id])
    wait_text = (
        f"{EMOJIS} <b>Hi2 Decorating...</b> Please wait some times {EMOJIS}\n\n"
        f"📥 Collected: <b>{total}</b> (Hi2: <b>{hi2}</b>, Telegmail: <b>{tele}</b>)"
    )

    if user_id in waiting_msgs:
        try:
            await waiting_msgs[user_id].edit_text(wait_text, parse_mode="HTML")
        except Exception:
            waiting_msgs[user_id] = await update.message.reply_text(wait_text, parse_mode="HTML")
    else:
        waiting_msgs[user_id] = await update.message.reply_text(wait_text, parse_mode="HTML")

    task = asyncio.create_task(send_combined(context, chat_id, user_id))
    pending_tasks[user_id] = task

# ── Web Server for Hosting (Render) ─────────────────────
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is alive and running 24/7!"

def run_web_server():
    port = int(os.environ.get('PORT', 8080))
    web_app.run(host='0.0.0.0', port=port)

# ── Main Function ───────────────────────────────────────
def main():
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN nahi mila!")
        return

    threading.Thread(target=run_web_server, daemon=True).start()
    print("🌐 Web server started for hosting...")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CallbackQueryHandler(button_click)) 
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ {BOT_NAME} start ho gaya...")
    app.run_polling()

if __name__ == "__main__":
    main()
