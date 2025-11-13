# -- coding: utf-8 --
import os
import logging
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from docx import Document

# --------------------- Load Environment ---------------------
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# --------------------- Logging ---------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --------------------- Load Knowledge Base ---------------------
def load_knowledge_docx(filepath="knowledge.docx"):
    data = []
    try:
        doc = Document(filepath)
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                data.append(text)
        logger.info(f"✅ Loaded {len(data)} knowledge entries from {filepath}")
    except Exception as e:
        logger.warning(f"⚠️ Could not load knowledge base: {e}")
    return data

knowledge_base = load_knowledge_docx()

# --------------------- Commands ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌿 Welcome to *GrowTogetherFrow AI Assistant!* 🌿\n\n"
        "Ask me anything about GrowTogetherFrow — I’ll answer from our official knowledge base 💬",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Just type your question — I’ll answer using GrowTogetherFrow’s knowledge 📚"
    )

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("✅ Chat history cleared successfully.")

# --------------------- Handle Messages ---------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    # Step 1: Try to find relevant paragraphs (keyword-based)
    matches = [para for para in knowledge_base if any(word in para.lower() for word in user_text.lower().split())]

    if matches:
        context_text = "\n".join(matches[:5])  # Top 5 relevant lines
    else:
        context_text = "\n".join(knowledge_base[:10])  # fallback

    try:
        prompt = (
            f"You are the official AI assistant for Grow Together Grow.\n"
            f"Answer clearly and only using the following information.\n\n"
            f"Knowledge:\n{context_text}\n\n"
            f"Question: {user_text}\n\n"
            f"Answer shortly in a friendly and motivational way."
        )

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        reply = completion.choices[0].message.content.strip()

    except Exception as e:
        logger.exception("OpenAI Error:")
        reply = "❌ Sorry, there was an issue generating a response. Please try again later."

    await update.message.reply_text(reply)

# --------------------- Main ---------------------
def main():
    if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
        print("❗ Missing TELEGRAM_TOKEN or OPENAI_API_KEY in .env file.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 GrowTogetherFrow Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
