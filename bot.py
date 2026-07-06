import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

def buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 AI", callback_data="ai"),
         InlineKeyboardButton("📚 BOOKS", callback_data="books")]
    ])

def search_books(q):
    try:
        r = requests.get(f"https://archive.org/advancedsearch.php?q={q}&output=json", timeout=10).json()
        books = []
        for d in r.get("response", {}).get("docs", [])[:5]:
            id_ = d.get("identifier")
            if id_:
                books.append({
                    "title": d.get("title"),
                    "link": f"https://archive.org/download/{id_}/{id_}.pdf"
                })
        return books
    except:
        return []

def ai(text):
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": "openai/gpt-4o-mini","messages":[{"role":"user","content":text}]}
        )
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "error"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose mode:", reply_markup=buttons())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["mode"] = q.data
    await q.message.reply_text(f"{q.data} mode active")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    mode = context.user_data.get("mode")

    if mode == "ai":
        await update.message.reply_text(ai(text), reply_markup=buttons())
        return

    if mode == "books":
        books = search_books(text)
        for b in books:
            await update.message.reply_text(
                f"{b['title']}",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Download", url=b["link"])]]
                ),
            )
        return

    await update.message.reply_text("Choose mode first", reply_markup=buttons())

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
