import os
import random
from fastapi import FastAPI, Request
from baleRobot import AsyncBaleClient, parse_update

app = FastAPI()
client = AsyncBaleClient(os.environ["BALE_TOKEN"])

# نگاشت متن دکمه‌ها به کلیدهای داخلی بازی
CHOICES = {
    "🪨 سنگ": "rock",
    "📄 کاغذ": "paper",
    "✂️ قیچی": "scissors",
}
CHOICE_NAMES = {v: k for k, v in CHOICES.items()}  # برعکس: rock -> 🪨 سنگ

def get_winner(user_choice: str, bot_choice: str) -> str:
    """تعیین برنده بازی"""
    if user_choice == bot_choice:
        return "مساوی شد! 🤝"
    wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
    if (user_choice, bot_choice) in wins:
        return "تو بردی! 🎉"
    return "من بردم! 🤖"

# --- ساخت کیبورد سفارشی پایین صفحه (Reply Keyboard) ---
def get_main_keyboard():
    """ساختار JSON کیبورد سفارشی برای ارسال به API بله"""
    return {
        "keyboard": [
            [{"text": "🪨 سنگ"}, {"text": "📄 کاغذ"}, {"text": "✂️ قیچی"}]
        ],
        "resize_keyboard": True,       # اندازه دکمه‌ها متناسب با متن باشد
        "one_time_keyboard": False,    # کیبورد بعد از انتخاب مخفی نشود
    }

@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = parse_update(await request.json())
        message = update.effective_message

        if message is None or message.text is None:
            return {"ok": True}

        text = message.text.strip()

        # --- دستور شروع ---
        if text == "/start":
            await client.send_message(
                message.chat_id,
                "به بازی سنگ کاغذ قیچی خوش آمدی! 🎮\n"
                "یکی از دکمه‌های زیر را انتخاب کن:",
                reply_markup=get_main_keyboard(),  # ارسال کیبورد سفارشی
            )
            return {"ok": True}

        # --- تشخیص انتخاب کاربر از روی متن دکمه ---
        if text in CHOICES:
            user_choice = CHOICES[text]
            bot_choice = random.choice(list(CHOICE_NAMES.keys()))
            result = get_winner(user_choice, bot_choice)

            await client.send_message(
                message.chat_id,
                f"تو: {text}\n"
                f"من: {CHOICE_NAMES[bot_choice]}\n\n"
                f"{result}",
            )
            return {"ok": True}

        # --- پیام‌های ناشناخته ---
        await client.send_message(
            message.chat_id,
            "لطفاً یکی از دکمه‌های پایین صفحه را انتخاب کن.",
        )
        return {"ok": True}

    except Exception as e:
        # لاگ کردن خطا برای دیباگ (در لاگ‌های Render دیده می‌شود)
        print(f"Error processing update: {e}")
        return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}
