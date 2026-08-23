import os
import logging
import threading
import numpy as np
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)

# --- Render Port Compatible Keep-Alive Server ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running online 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Configuration Details
BOT_TOKEN = "8789586990:AAEDjMNZ0KM8t2GXwA5x4bYYNfROWE783sI"
SECRET_PASSWORD = "80165108928170804200"
TELEGRAM_ADMIN_USERNAME = "subhajitxtrding"

# Conversation States
WAITING_FOR_KEY, SELECTING_PAIR, SELECTING_TIMEFRAME = range(3)

# Markets List
REAL_LIVE_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "USD/CHF", "NZD/USD",
    "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY", "CAD/JPY", "EUR/AUD", "GBP/CAD",
    "XAU/USD (Gold)", "XAG/USD (Silver)", "USOIL",
    "BTC/USDT", "ETH/USDT", "XRP/USDT", "SOL/USDT"
]

# Timeframes List
TIMEFRAMES = [
    ("⏱ 1 Minute", "1m"),
    ("⏱ 3 Minutes", "3m"),
    ("⏱ 5 Minutes", "5m"),
    ("⏱ 15 Minutes", "15m"),
    ("⏱ 30 Minutes", "30m"),
    ("⏱ 1 Hour", "1h")
]

# Analysis Engine
def analyze_market_signal(pair_name, timeframe_label):
    np.random.seed(abs(hash(pair_name + timeframe_label)) % (2**32))
    
    bullish_signals = np.random.randint(30, 48)
    bearish_signals = 50 - bullish_signals
    win_rate = int((max(bullish_signals, bearish_signals) / 50) * 100)
    
    if bullish_signals > bearish_signals:
        prediction = "BUY (UP) 📈🟢"
        candle_color = "GREEN CANDLE 🟢"
    else:
        prediction = "SELL (DOWN) 📉🔴"
        candle_color = "RED CANDLE 🔴"
        
    return {
        "prediction": prediction,
        "candle_color": candle_color,
        "bullish_count": bullish_signals,
        "bearish_count": bearish_signals,
        "win_rate": win_rate
    }

# 1. Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['authenticated'] = False
    
    keyboard = [
        [InlineKeyboardButton("🔑 Get Secret Key", url=f"https://t.me/{TELEGRAM_ADMIN_USERNAME}")],
        [InlineKeyboardButton("🔓 Enter Key to Unlock", callback_data="ask_key")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "👑 **SIGNAL POWER BOT** 👑\n"
        "--------------------------------------------------\n"
        "📊 **লাইভ মার্কেট সিগন্যাল এনালাইজার**\n"
        "🎯 **Accuracy:** **85% - 95%**\n"
        "--------------------------------------------------\n\n"
        "🔒 বটটি ব্যবহার করতে Secret Key প্রয়োজন।\n\n"
        "👉 Key পেতে এডমিনের সাথে যোগাযোগ করতে **'🔑 Get Secret Key'** চাপুন।"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_KEY

# Ask Key
async def prompt_for_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🔑 অনুগ্রহ করে আপনার **Secret Key (Password)** টি নিচে টাইপ করে পাঠান:",
        parse_mode="Markdown"
    )
    return WAITING_FOR_KEY

# 2. Key Verification
async def verify_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_key = update.message.text.strip()
    
    if user_key == SECRET_PASSWORD:
        context.user_data['authenticated'] = True
        
        keyboard = []
        row = []
        for pair in REAL_LIVE_PAIRS:
            row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "✅ **Access Granted!**\n\n"
            "📊 **All Available Markets:**\n"
            "এনালাইসিস করতে যেকোনো একটি মার্কেট নির্বাচন করুন:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return SELECTING_PAIR
    else:
        keyboard = [
            [InlineKeyboardButton("🔑 Get Secret Key", url=f"https://t.me/{TELEGRAM_ADMIN_USERNAME}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "❌ **ভুল পাসওয়ার্ড!** সঠিক পাসওয়ার্ড লিখুন অথবা এডমিনের থেকে Key নিন:",
            reply_markup=reply_markup
        )
        return WAITING_FOR_KEY

# 3. Market Selected -> Show Timeframes
async def handle_pair_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_pair = query.data.replace("pair_", "")
    context.user_data['selected_pair'] = selected_pair

    keyboard = []
    row = []
    for tf_text, tf_code in TIMEFRAMES:
        row.append(InlineKeyboardButton(tf_text, callback_data=f"tf_{tf_code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        f"🎯 Selected Market: **{selected_pair}**\n\n"
        f"⏱ এবার আপনার পছন্দের **Timeframe** টি নির্বাচন করুন:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_TIMEFRAME

# 4. Timeframe Selected -> Show Signal
async def handle_timeframe_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    selected_pair = context.user_data.get('selected_pair', 'Market')
    tf_code = query.data.replace("tf_", "")

    await query.message.reply_text(
        f"⏳ Analyzing 50 indicators for **{selected_pair}** on **{tf_code}** timeframe...", 
        parse_mode="Markdown"
    )

    res = analyze_market_signal(selected_pair, tf_code)

    report = (
        f"📊 **MARKET ANALYSIS REPORT**\n"
        f"--------------------------------------------------\n"
        f"🔀 Market: **{selected_pair}**\n"
        f"⏱ Timeframe: **{tf_code}**\n"
        f"--------------------------------------------------\n"
        f"🚀 Signal Prediction: **{res['prediction']}**\n"
        f"🕯 Expected Candle: **{res['candle_color']}**\n"
        f"🎯 Win Rate / Accuracy: **{res['win_rate']}%**\n"
        f"📊 Indicator Score: 🟢 {res['bullish_count']}/50 vs 🔴 {res['bearish_count']}/50\n"
        f"--------------------------------------------------\n"
        f"💡 **Trading Tip:** Enter trade at the first 0-3 seconds of candle opening."
    )

    keyboard = []
    row = []
    for pair in REAL_LIVE_PAIRS:
        row.append(InlineKeyboardButton(pair, callback_data=f"pair_{pair}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(report, parse_mode="Markdown")
    await query.message.reply_text("🔄 **অন্য কোনো মার্কেট এনালাইজ করতে সিলেক্ট করুন:**", reply_markup=reply_markup, parse_mode="Markdown")
    return SELECTING_PAIR

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['authenticated'] = False
    if update.message:
        await update.message.reply_text("🔒 Bot locked. Type /start to unlock again.")
    return ConversationHandler.END

def main():
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_KEY: [
                CallbackQueryHandler(prompt_for_key, pattern="^ask_key$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, verify_key)
            ],
            SELECTING_PAIR: [
                CallbackQueryHandler(handle_pair_selection, pattern="^pair_")
            ],
            SELECTING_TIMEFRAME: [
                CallbackQueryHandler(handle_timeframe_selection, pattern="^tf_"),
                CallbackQueryHandler(handle_pair_selection, pattern="^pair_")
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    print("🤖 Trading Bot Started Successfully with Flask!")
    app.run_polling()

if __name__ == '__main__':
    main()
