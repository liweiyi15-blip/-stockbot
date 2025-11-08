import os
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests
import threading

# 环境变量
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")

if not TELEGRAM_TOKEN or not FINNHUB_TOKEN:
    raise RuntimeError("请设置 TELEGRAM_TOKEN 和 FINNHUB_TOKEN 环境变量！")

app = Flask(__name__)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 消息处理
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("$"):
        return

    symbol = text[1:].upper()
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}"
    
    try:
        data = requests.get(url).json()
        if data.get("c") is not None:
            price = data["c"]
            change = data["d"]
            percent = data["dp"]
            emoji = "📈" if change >= 0 else "📉"
            change_sign = "+" if change >= 0 else ""
            await update.message.reply_text(
                f"{emoji} *{symbol}*\n"
                f"当前价: `${price:.2f}`\n"
                f"涨跌: `{change_sign}{change:.2f} ({change_sign}{percent:.2f}%)`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("未找到该股票代码")
    except:
        await update.message.reply_text("查询失败")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用股票查询机器人！\n"
        "输入如 `$AAPL`、`$TSLA`、`$00700` 即可查询实时股价。"
    )

# 注册处理器
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook 路由
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK', 200

# 设置 webhook
def set_webhook():
    url = f"https://{os.getenv('RAILWAY_STATIC_URL')}/{TELEGRAM_TOKEN}"
    application.bot.set_webhook(url=url)
    print(f"Webhook 已设置: {url}")

if __name__ == '__main__':
    threading.Thread(target=set_webhook).start()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
