# bot.py
import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

from products import PRODUCT_DETAILS, VOSK_OPTIONS
from keyboards import get_keyboard, get_detail_keyboard, get_vosk_keyboard

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

user_orders = {}
awaiting_contact = set()
last_sent_message = {}

async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not await check_subscription(user_id, context):
        markup = ReplyKeyboardMarkup([[KeyboardButton("🔄 Tekshirish")]], resize_keyboard=True)
        await update.message.reply_text(
            f"🔐 Botdan foydalanish uchun quyidagi kanalda obuna bo‘ling:\n👉 <a href='https://t.me/{CHANNEL_USERNAME[1:]}'>{CHANNEL_USERNAME}</a>\n\n"
            "So‘ng “🔄 Tekshirish” tugmasini bosing.",
            parse_mode='HTML', reply_markup=markup, disable_web_page_preview=True)
        return

    user_orders[user_id] = []
    awaiting_contact.discard(user_id)
    last_sent_message.pop(user_id, None)
    await update.message.reply_text("Xush kelibsiz!\nMahsulotni tanlang:", reply_markup=get_keyboard())

async def handle_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    match text:
        case "🔄 Tekshirish":
            if await check_subscription(user_id, context):
                await update.message.reply_text("✅ Obuna tasdiqlandi.", reply_markup=get_keyboard())
            else:
                await update.message.reply_text("❗ Hali ham obuna emassiz.")
        case "🛒 Savatchaga qo‘shish":
            prod = context.user_data.get("last_product")
            if prod:
                user_orders.setdefault(user_id, []).append(prod)
                await update.message.reply_text(f"✅ Savatchaga qo‘shildi: {prod}", reply_markup=get_keyboard())
            else:
                await update.message.reply_text("❗ Hech qanday mahsulot tanlanmagan.")
        case "🔙 Orqaga":
            await update.message.reply_text("↩️ Asosiy menyu:", reply_markup=get_keyboard())
        case "✨ Vosk":
            await update.message.reply_text("✨ Vosk variantlarini tanlang:", reply_markup=get_vosk_keyboard())
        case "✅ Buyurtmani tasdiqlash":
            if not user_orders.get(user_id):
                await update.message.reply_text("❗ Savatchangiz bo‘sh.")
                return
            contact_btn = KeyboardButton("📱 Raqamni yuborish", request_contact=True)
            markup = ReplyKeyboardMarkup([[contact_btn]], resize_keyboard=True, one_time_keyboard=True)
            awaiting_contact.add(user_id)
            await update.message.reply_text("📞 Telefon raqamingizni yuboring:", reply_markup=markup)
        case "❌ Bekor qilish":
            user_orders[user_id] = []
            awaiting_contact.discard(user_id)
            if user_id in last_sent_message:
                try:
                    await context.bot.edit_message_text(chat_id=GROUP_ID, message_id=last_sent_message[user_id],
                                                        text="❌ <b>Buyurtma bekor qilindi</b>", parse_mode='HTML')
                except:
                    pass
                last_sent_message.pop(user_id)
            await update.message.reply_text("❌ Buyurtma bekor qilindi.", reply_markup=get_keyboard())
        case _ if text in PRODUCT_DETAILS:
            details = PRODUCT_DETAILS[text]
            context.user_data["last_product"] = text
            msg = f"{details['description']}\n{details['price_info']}"
            await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_detail_keyboard())
        case _ if text in VOSK_OPTIONS:
            if text == "🔙 Orqaga":
                await update.message.reply_text("↩️ Asosiy menyuga qaytdingiz:", reply_markup=get_keyboard())
            else:
                user_orders.setdefault(user_id, []).append(text)
                await update.message.reply_text(f"🛒 Savatchaga qo‘shildi: {text}")
        case _:
            await update.message.reply_text("Iltimos, tugmalardan foydalaning.")

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if user_id not in awaiting_contact:
        return

    phone_number = update.message.contact.phone_number
    order = user_orders.get(user_id, [])
    order_text = "\n".join(order)

    msg = (
        f"🛍 <b>Yangi buyurtma!</b>\n"
        f"👤 <b>{user.full_name}</b>\n"
        f"🆔 <code>{user.id}</code>\n"
        f"📞 <b>Raqam:</b> {phone_number}\n"
        f"📦 Buyurtmalar:\n{order_text}"
    )

    sent = await context.bot.send_message(chat_id=GROUP_ID, text=msg, parse_mode='HTML')
    last_sent_message[user_id] = sent.message_id

    await update.message.reply_text("✅ Buyurtma va raqamingiz qabul qilindi.", reply_markup=get_keyboard())
    user_orders[user_id] = []
    awaiting_contact.discard(user_id)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selection))

    print(" Bot ishga tushdi...")
    app.run_polling()
