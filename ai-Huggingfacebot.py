import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from transformers import AutoModelForCausalLM, AutoTokenizer

# کلیدهای API
TELEGRAM_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
HUGGINGFACE_API_KEY = "HUGGINGFACE_API_KEY"

# لیست کاربران مجاز (ID کاربران تلگرام)
ALLOWED_USERS = [2016507333,35657678994]  # شناسه‌های کاربران مجاز

# اتصال به دیتابیس SQLite
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

# ایجاد جدول ذخیره مکالمات
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

#Hugging Face دانلود مدل و توکنایزر از 
model_name = "EleutherAI/gpt-neo-125M"  
model = AutoModelForCausalLM.from_pretrained(model_name, use_auth_token=HUGGINGFACE_API_KEY)
tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=HUGGINGFACE_API_KEY)

def save_conversation(user_id, username, user_message, ai_response):
    """
   SQLite ذخیره مکالمات در دیتابیس 
    """
    cursor.execute("""
        INSERT INTO history (user_id, username, user_message, ai_response)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, user_message, ai_response))
    conn.commit()

def generate_response(prompt):
    """
   Hugging Face تولید پاسخ از مدل 
    """
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=100, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
   /start دستور : پیام خوش‌آمدگویی
    """
    await update.message.reply_text(
        "سلام! من یک ربات هوش مصنوعی هستم. هر سوالی داری بپرس. برای خروج، پیام جدیدی نفرست. 😄"
    )

async def ask_gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    user_message = update.message.text

    # بررسی دسترسی کاربر
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("متأسفم، شما اجازه استفاده از این ربات را ندارید.")
        return

    #Hugging Face ارسال پیام به مدل 
    try:
        ai_response = generate_response(user_message)
    except Exception as e:
        ai_response = f"خطایی رخ داده است: {e}"

    # ذخیره مکالمه در دیتابیس
    save_conversation(user_id, username, user_message, ai_response)

    # ارسال پاسخ به کاربر
    await update.message.reply_text(ai_response)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
   /help دستور : ارائه راهنمایی
    """
    await update.message.reply_text(
        "من یک ربات هوش مصنوعی هستم! می‌تونی سوالاتت رو بپرسی و من جوابت رو میدم.\n"
        "دستورات موجود:\n"
        "/start - شروع\n"
        "/help - راهنما"
    )

def main():
    """
    اجرای ربات تلگرام
    """
    # ساخت اپلیکیشن تلگرام
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # مدیریت دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gpt))

    # اجرای ربات
    print("ok")
    app.run_polling()

if __name__ == "__main__":
    main()
