import os
import time
import threading
import logging
import ccxt
import pandas as pd
import pandas_ta as ta
from flask import Flask, jsonify
from logging.handlers import RotatingFileHandler
import requests

# --- معلومات تيليجرام الخاصة بك ---
TELEGRAM_TOKEN = "8672044760:AAFcR9D9kzKDlsCvnBPac-h6rIOoiZBwwUU"
CHAT_ID = "8950181264"

# إعداد السجلات الاحترافية مع تدوير الملفات لتفادي امتلاء القرص
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
file_handler = RotatingFileHandler('enterprise_trading_bot.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = Flask(__name__)

# إعدادات أزواج العملات والمؤشرات الفنية الاحترافية
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT', 'BNB/USDT']
TIMEFRAME = '1h'

def send_telegram_alert(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            logger.error(f"فشل إرسال تنبيه تيليجرام: {response.text}")
    except Exception as e:
        logger.error(f"خطأ في الاتصال بتيليجرام: {e}")

def analyze_market():
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    
    while True:
        try:
            logger.info("بدء جلسة تحليل السوق الاحترافية...")
            for symbol in SYMBOLS:
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    
                    # حساب المؤشرات الفنية المتقدمة
                    df['rsi'] = ta.rsi(df['close'], length=14)
                    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
                    df = pd.concat([df, macd], axis=1)
                    
                    last_row = df.iloc[-1]
                    
                    price = last_row['close']
                    rsi = last_row['rsi']
                    macd_hist = last_row.get('MACDh_12_26_9', 0)
                    
                    # استراتيجية إشارات التداول عالية الدقة
                    signal = None
                    if rsi < 35 and macd_hist > 0:
                        signal = "🟢 *إشارة شراء قوية (BUY)*"
                    elif rsi > 65 and macd_hist < 0:
                        signal = "🔴 *إشارة بيع قوية (SELL)*"
                        
                    if signal:
                        msg = (
                            f"🤖 *Quantum Elite Pro v101.0*\n"
                            f"----------------------------------\n"
                            f"العملة: *{symbol}*\n"
                            f"الإشارة: {signal}\n"
                            f"السعر الحالي: `{price}` USD\n"
                            f"مؤشر RSI: `{round(rsi, 2)}`\n"
                            f"----------------------------------\n"
                            f"⚡ نظام الحماية والتداول الذكي فعال."
                        )
                        send_telegram_alert(msg)
                        logger.info(f"تم إرسال إشارة لـ {symbol}: {signal}")
                        
                except Exception as ex:
                    logger.error(f"خطأ في تحليل العملة {symbol}: {ex}")
                
                time.sleep(5)
                
        except Exception as err:
            logger.error(f"الحلقة الرئيسية واجهت خطأ: {err}")
            
        # الانتظار لمدة ساعة قبل الدورة القادمة
        time.sleep(3600)

@app.route('/')
def health_check():
    return jsonify({"status": "active", "bot": "Quantum Elite Pro v101.0", "status_code": 200})

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    # تشغيل بوت التداول في خلفية مستقلة
    trading_thread = threading.Thread(target=analyze_market)
    trading_thread.daemon = True
    trading_thread.start()
    
    # تشغيل خادم الويب للحفاظ على نشاط البوت
    run_flask()
