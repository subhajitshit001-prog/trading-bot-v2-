import time
import requests
import pandas as pd
import numpy as np
import yfinance as yf

# ==========================================
# CONFIGURATION / কনফিগারেশন
# ==========================================
TELEGRAM_BOT_TOKEN = '8789586990:AAEDjMNZ0KM8t2GXwA5x4bYYNfROWE783sI'
TELEGRAM_CHAT_ID = '8583380235'

# জনপ্রিয় ও সেরা ফরেক্স পেয়ারসমূহ
SYMBOLS = [
    'EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 
    'USDCAD=X', 'USDCHF=X', 'NZDUSD=X', 'EURGBP=X'
]

# টাইমফ্রেম নির্বাচন (1m, 5m, 15m)
TIMEFRAMES = ['1m', '5m', '15m']

# আগের সিগন্যাল ট্র্যাক রাখার জন্য
last_processed_signals = {}

# ==========================================
# TELEGRAM MESSAGE FUNCTION
# ==========================================
def send_telegram_message(message):
    """টেলিগ্রামে মেসেজ পাঠানোর ফাংশন"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

# ==========================================
# INDICATOR CALCULATIONS
# ==========================================
def calculate_indicators(df):
    """RSI, EMA, এবং Bollinger Bands হিসাব করার ফাংশন"""
    # 1. RSI (14 period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # 2. EMA (Short = 9, Long = 21)
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()

    # 3. Bollinger Bands (20 period)
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['STD_20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['SMA_20'] + (df['STD_20'] * 2)
    df['BB_Lower'] = df['SMA_20'] - (df['STD_20'] * 2)

    return df

# ==========================================
# STRATEGY ANALYSIS LOGIC
# ==========================================
def analyze_market(symbol, timeframe):
    """মার্কেট ডাটা ফেচ করে স্ট্র্যাটেজি দিয়ে সিগন্যাল তৈরি করা"""
    global last_processed_signals

    try:
        # ডাটা লোড করা
        df = yf.download(tickers=symbol, period='1d', interval=timeframe, progress=False)
        
        if df.empty or len(df) < 30:
            return

        # ইনডিকেটর হিসাব করা
        df = calculate_indicators(df)

        # সর্বশেষ সম্পন্ন হওয়া ক্যান্ডেল (Last Closed Candle)
        latest_candle = df.iloc[-2]
        candle_time = str(latest_candle.name)
        tracking_key = f"{symbol}_{timeframe}"

        # ১. ডুপ্লিকেট সিগন্যাল প্রতিরোধ (একই বারে বারবার যেন না পাঠায়)
        if last_processed_signals.get(tracking_key) == candle_time:
            return 

        close_price = float(latest_candle['Close'])
        rsi = float(latest_candle['RSI'])
        ema9 = float(latest_candle['EMA_9'])
        ema21 = float(latest_candle['EMA_21'])
        bb_upper = float(latest_candle['BB_Upper'])
        bb_lower = float(latest_candle['BB_Lower'])

        signal = None
        reasons = []

        # UP SIGNAL (BUY) শর্ত:
        if rsi < 35 and close_price <= bb_lower * 1.0005:
            signal = "🟢 CALL / BUY (UP)"
            reasons.append("RSI Oversold Level (<35)")
            reasons.append("Price at Lower Bollinger Band")
        elif ema9 > ema21 and rsi < 50 and close_price > bb_lower:
            signal = "🟢 CALL / BUY (UP)"
            reasons.append("EMA Golden Cross (Bullish Trend)")

        # DOWN SIGNAL (SELL) শর্ত:
        if rsi > 65 and close_price >= bb_upper * 0.9995:
            signal = "🔴 PUT / SELL (DOWN)"
            reasons.append("RSI Overbought Level (>65)")
            reasons.append("Price at Upper Bollinger Band")
        elif ema9 < ema21 and rsi > 50 and close_price < bb_upper:
            signal = "🔴 PUT / SELL (DOWN)"
            reasons.append("EMA Death Cross (Bearish Trend)")

        # সিগন্যাল মিললে মেসেজ তৈরি ও সেন্ড করা
        if signal:
            pair_name = symbol.replace('=X', '')
            message = (
                f"🚨 **NEW TRADING SIGNAL** 🚨\n\n"
                f"📊 **Asset:** `{pair_name}`\n"
                f"📈 **Direction:** {signal}\n"
                f"💵 **Price:** `{close_price:.5f}`\n"
                f"📊 **RSI:** `{rsi:.2f}`\n"
                f"⏱️ **Timeframe:** `{timeframe}`\n\n"
                f"🔍 **Confluence Reasons:**\n" + 
                "\n".join([f"• {r}" for r in reasons]) + "\n\n"
                f"⚠️ *Trading involves risk. Practice proper risk management!*"
            )
            
            # টেলিগ্রামে পাঠানো
            send_telegram_message(message)
            print(f"[{candle_time}] [{timeframe}] Signal sent for {pair_name}: {signal}")

            # বারের টাইম আপডেট করা
            last_processed_signals[tracking_key] = candle_time

    except Exception as e:
        print(f"Error analyzing {symbol} on {timeframe}: {e}")

# ==========================================
# MAIN LOOP
# ==========================================
if __name__ == "__main__":
    print("🤖 Trading Bot Started running...")
    send_telegram_message("🤖 **Trading Signal Bot Activated!** Scanning Forex markets...")

    while True:
        for tf in TIMEFRAMES:
            for symbol in SYMBOLS:
                analyze_market(symbol, tf)
                time.sleep(1) # API লিমিট এড়াতে ১ সেকেন্ড বিরতি
        
        # প্রতিটি চক্রের পর ২০ সেকেন্ড বিরতি
        time.sleep(20)
