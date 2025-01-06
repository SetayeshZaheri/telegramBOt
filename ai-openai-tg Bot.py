import openai
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# API Keys
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
openai.api_key = OPENAI_API_KEY

# access users
ALLOWED_USERS = [123456789, 987654321]

#conect to SQLite Database
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# create a tabel for saving conversations
cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        user_message TEXT,
        ai_response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

def save_conversation(user_id, username, user_message, ai_response):
    """
   saving conversations in SQLite
    """
    cursor.execute("""
        INSERT INTO history (user_id, username, user_message, ai_response)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, user_message, ai_response))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start: say hello
    """
    await update.message.reply_text(
        "Hi😄 I`m a AI Bot, How can I help you?"
    )

async def ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Receive user messsage and sen to openAI API and answer 
    """
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_message = update.message.text

    # Check user access
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("Sorry! you are not authorized to used this bot")
        return

    # send message to OpenAI API
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]
        )
        ai_response = response['choices'][0]['message']['content']
    except Exception as e:
        ai_response = f"Something wrong   : {e}"

    # saving converstation in database
    save_conversation(user_id, username, user_message, ai_response)

    #  send answer to user  
    await update.message.reply_text(ai_response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
     /help: Helping 
    """
    await update.message.reply_text(
        "I am a intelligence robot, you can ask me your questions!.\n"
        " available commands:\n"
        "/start - start\n"
        "/help - help"
    )

def main():
    """
      Run thi telegram Bot
    """
    # create the telegram app
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Manage orders 
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gpt))

    # Run the Bot
    print("Bot is ready")
    app.run_polling()

if __name__ == "__main__":
    main()
