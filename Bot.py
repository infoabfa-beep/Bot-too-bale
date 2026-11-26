import os, random
from fastapi import FastAPI, Request
from baleRobot import AsyncBaleClient, parse_update

app = FastAPI()
client = AsyncBaleClient(os.environ["BALE_TOKEN"])

CHOICES = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}

def winner(user, bot):
    if user == bot: return "مساوی شد! 🤝"
    wins = {("rock","scissors"), ("paper","rock"), ("scissors","paper")}
    return "تو بردی! 🎉" if (user, bot) in wins else "من بردم! 🤖"

@app.post("/webhook")
async def webhook(request: Request):
    update = parse_update(await request.json())
    msg = update.effective_message
    if not msg: return {"ok": True}

    # /start → نمایش دکمه‌ها
    if msg.text == "/start":
        await client.send_message(
            msg.chat_id,
            "بازی سنگ کاغذ قیچی! انتخاب کن:",
            reply_markup={
                "inline_keyboard": [[
                    {"text": "🪨 سنگ", "callback_data": "rock"},
                    {"text": "📄 کاغذ", "callback_data": "paper"},
                    {"text": "✂️ قیچی", "callback_data": "scissors"},
                ]]
            }
        )
        return {"ok": True}

    # کلیک روی دکمه
    if update.callback_query:
        cq = update.callback_query
        user = cq.data
        bot = random.choice(list(CHOICES.keys()))
        result = winner(user, bot)
        await client.answer_callback_query(cq.id)
        await client.send_message(
            cq.message.chat.id,
            f"تو: {CHOICES[user]}\nمن: {CHOICES[bot]}\n\n{result}"
        )
    return {"ok": True}

@app.get("/")
async def health(): return {"status": "ok"}
