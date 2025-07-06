from telegram import ReplyKeyboardMarkup
from products import PRODUCTS, VOSK_OPTIONS

def chunk(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def get_keyboard():
    rows = chunk(PRODUCTS, 2)
    rows.append(["✅ Buyurtmani tasdiqlash", "❌ Bekor qilish"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_vosk_keyboard():
    rows = chunk(VOSK_OPTIONS[:-1], 2)
    rows.append(["🔙 Orqaga"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def get_detail_keyboard():
    return ReplyKeyboardMarkup([["🛒 Savatchaga qo‘shish", "🔙 Orqaga"]], resize_keyboard=True)
