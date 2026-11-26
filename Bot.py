import os
import random
from fastapi import FastAPI, Request
from pyrobale import Client
from pyrobale.objects import Message, CallbackQuery, UpdatesTypes

app = FastAPI()
bot = Client(os.environ["BALE_TOKEN"])

CHOICES = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}

def winner(user, bot_choice):
    if user == bot_choice: return "مساوی شد! 🤝"
    wins = {("rock","scissors"), ("paper","rock"), ("scissors","paper")}
    return "تو بردی! 🎉" if (user, bot_choice) in wins else "من بردم! 🤖"

# هندلر دستور /start
@bot.on_command("start")
async def start_handler(message: Message):
    await message.reply(
        "بازی سنگ کاغذ قیچی! انتخاب کن:",
        reply_markup={
            "inline_keyboard": [[
                {"text": "🪨 سنگ", "callback_data": "rock"},
                {"text": "📄 کاغذ", "callback_data": "paper"},
                {"text": "✂️ قیچی", "callback_data": "scissors"},
            ]]
        }
    )

# هندلر کلیک روی دکمه‌ها
@bot.on_callback_query()
async def callback_handler(cq: CallbackQuery):
    user_choice = cq.data
    bot_choice = random.choice(list(CHOICES.keys()))
    result = winner(user_choice, bot_choice)
    
    await cq.answer()
    await cq.message.reply(
        f"تو: {CHOICES[user_choice]}\nمن: {CHOICES[bot_choice]}\n\n{result}"
    )

# نقطه اتصال Webhook برای Render
@app.post("/webhook")
async def webhook(request: Request):
    update_data = await request.json()
    # پردازش آپدیت با Pyrobale
    update = bot.parse_update(update_data)
    await bot.process_update(update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}
