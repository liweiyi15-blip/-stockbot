import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import requests

# 从环境变量读取 Token（安全！）
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FINNHUB_TOKEN = os.getenv("FINNHUB_TOKEN")

# 检查 Token 是否存在
if not TELEGRAM_TOKEN or not FINNHUB_TOKEN:
    raise RuntimeError("请在环境变量中设置 TELEGRAM_TOKEN 和 FINNHUB_TOKEN！")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # 只响应以 $ 开头的消息
    if not text.startswith("$"):
        return

    symbol = text[1:].upper()
    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_TOKEN}"
    
    try:
        response = requests.get(url)
        data = response.json()

        if data.get("c") is not None:
            price = data["c"]
            change = data["d"]
            percent = data["dp"]

            # 涨跌图标
            emoji = "Up" if change >= 0 else "Down"
            change_sign = "+" if change >= 0 else ""

            await update.message.reply_text(
                f"{emoji} *{symbol}*\n"
                f"当前价: `${price:.2f}`\n"
                f"涨跌: `{change_sign}{change:.2f} ({change_sign}{percent:.2f}%)`",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("未找到该股票代码，请检查输入。")
    except Exception as e:
        await update.message.reply_text("查询失败，请稍后再试。")
        print(f"API Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "欢迎使用股票查询机器人！\n"
        "输入如 `$AAPL`、`$TSLA`、`$00700` 即可查询实时股价。"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("股票机器人已启动...")
    app.run_polling()