import os
import random
import asyncio
from fastapi import FastAPI, Request
from baleRobot import AsyncBaleClient, parse_update, InlineKeyboardMarkup

app = FastAPI()
client = AsyncBaleClient(os.environ["BALE_TOKEN"])
BOT_USERNAME = os.environ.get("BOT_USERNAME", "YourBotUsername")

# ---------------------------------------------------------
# حافظه
# ---------------------------------------------------------
active_games = {}
match_queue = []
pending_invites = {}
user_game = {}

CHOICES = {"🪨 سنگ": "rock", "📄 کاغذ": "paper", "✂️ قیچی": "scissors"}
CHOICE_NAMES = {"rock": "🪨 سنگ", "paper": "📄 کاغذ", "scissors": "✂️ قیچی"}

def get_winner(c1, c2):
    if c1 == c2: return "tie"
    wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
    return "p1" if (c1, c2) in wins else "p2"

# ---------------------------------------------------------
# منوی اصلی (قشنگ‌تر)
# ---------------------------------------------------------
def main_menu():
    return (
        "🎮 **بازی سنگ کاغذ قیچی**\n"
        "━━━━━━━━━━━━━━━\n"
        "🤖 **مسابقه با ربات** — تا ۱۰ امتیاز، سریع و بامزه\n"
        "👥 **بازی با دوست** — لینک دعوت اختصاصی\n"
        "⏳ **جستجوی حریف** — وارد صف شو و منتظر بمان\n"
        "❌ **لغو** — خروج از صف یا بازی\n"
        "━━━━━━━━━━━━━━━\n"
        "یکی از دکمه‌های پایین را بزن 👇"
    )

def main_keyboard():
    return {
        "keyboard": [
            [{"text": "🤖 مسابقه با ربات"}],
            [{"text": "👥 بازی با دوست (لینک)"}],
            [{"text": "⏳ جستجوی حریف (صف)"}],
            [{"text": "❌ لغو / خروج"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
    }

def choice_keyboard():
    return InlineKeyboardMarkup.quick([
        [("🪨 سنگ", "rock"), ("📄 کاغذ", "paper"), ("✂️ قیچی", "scissors")]
    ])

async def send(chat_id, text, reply_markup=None):
    await client.send_message(chat_id, text, reply_markup=reply_markup)

# ---------------------------------------------------------
# بازی با ربات
# ---------------------------------------------------------
async def start_bot_game(user_id, chat_id):
    game_id = f"bot_{user_id}_{random.randint(1000, 9999)}"
    active_games[game_id] = {
        "p1": user_id, "p2": "BOT",
        "score1": 0, "score2": 0,
        "p1_choice": None, "p2_choice": None,
        "is_bot": True,
    }
    user_game[user_id] = game_id
    await send(chat_id, "🤖 **مسابقه با ربات شروع شد!**\nهر دور انتخاب کن:", reply_markup=choice_keyboard())

async def process_choice(user_id, chat_id, choice, game_id):
    game = active_games.get(game_id)
    if not game:
        await send(chat_id, "بازی فعالی پیدا نشد.")
        return

    # بازی با ربات
    if game.get("is_bot"):
        if user_id != game["p1"]:
            return
        bot_choice = random.choice(list(CHOICE_NAMES.keys()))
        res = get_winner(choice, bot_choice)

        if res == "p1":
            game["score1"] += 1
            msg = f"تو: {CHOICE_NAMES[choice]}\nمن: {CHOICE_NAMES[bot_choice]}\n\n🎉 **تو بردی!**"
        elif res == "p2":
            game["score2"] += 1
            msg = f"تو: {CHOICE_NAMES[choice]}\nمن: {CHOICE_NAMES[bot_choice]}\n\n😔 **من بردم!**"
        else:
            msg = f"تو: {CHOICE_NAMES[choice]}\nمن: {CHOICE_NAMES[bot_choice]}\n\n🤝 **مساوی!**"

        msg += f"\n\n📊 امتیاز: تو {game['score1']} — {game['score2']} ربات"

        if game["score1"] >= 10 or game["score2"] >= 10:
            if game["score1"] >= 10:
                msg += "\n\n🏆 **تبریک! برنده‌ی مسابقه شدی!**"
            else:
                msg += "\n\n😅 **ربات برنده شد. دفعه بعد جبران کن!**"
            user_game.pop(user_id, None)
            active_games.pop(game_id, None)
            await send(chat_id, msg, reply_markup=main_keyboard())
        else:
            await send(chat_id, msg, reply_markup=choice_keyboard())
        return

    # بازی دو نفره
    if user_id == game["p1"]:
        if game["p1_choice"] is not None:
            await send(chat_id, "قبلاً انتخاب کردی! صبر کن حریف انتخاب کنه.")
            return
        game["p1_choice"] = choice
    elif user_id == game["p2"]:
        if game["p2_choice"] is not None:
            await send(chat_id, "قبلاً انتخاب کردی! صبر کن حریف انتخاب کنه.")
            return
        game["p2_choice"] = choice
    else:
        return

    await send(chat_id, f"انتخاب تو ثبت شد: {CHOICE_NAMES[choice]}. منتظر حریف...")

    if game["p1_choice"] and game["p2_choice"]:
        c1, c2 = game["p1_choice"], game["p2_choice"]
        res = get_winner(c1, c2)
        if res == "p1":
            game["score1"] += 1
            msg1 = f"🎉 **تو بردی!** ({CHOICE_NAMES[c1]} در مقابل {CHOICE_NAMES[c2]})"
            msg2 = f"😔 حریف برنده شد. ({CHOICE_NAMES[c2]} در مقابل {CHOICE_NAMES[c1]})"
        elif res == "p2":
            game["score2"] += 1
            msg1 = f"😔 حریف برنده شد. ({CHOICE_NAMES[c1]} در مقابل {CHOICE_NAMES[c2]})"
            msg2 = f"🎉 **تو بردی!** ({CHOICE_NAMES[c2]} در مقابل {CHOICE_NAMES[c1]})"
        else:
            msg1 = msg2 = f"🤝 **مساوی!** (هر دو {CHOICE_NAMES[c1]})"

        game["p1_choice"] = None
        game["p2_choice"] = None

        await send(game["p1"], f"{msg1}\n\n📊 امتیاز: تو {game['score1']} — {game['score2']} حریف")
        await send(game["p2"], f"{msg2}\n\n📊 امتیاز: تو {game['score2']} — {game['score1']} حریف")

        if game["score1"] >= 10 or game["score2"] >= 10:
            winner_id = game["p1"] if game["score1"] >= 10 else game["p2"]
            loser_id = game["p2"] if winner_id == game["p1"] else game["p1"]
            await send(winner_id, f"🏆 **برنده مسابقه شدی!** {game['score1']} — {game['score2']}", reply_markup=main_keyboard())
            await send(loser_id, f"مسابقه تمام شد. 😔\n📊 امتیاز نهایی: {game['score2']} — {game['score1']}", reply_markup=main_keyboard())
            for uid in [game["p1"], game["p2"]]:
                user_game.pop(uid, None)
            active_games.pop(game_id, None)
        else:
            await send(game["p1"], "دور بعد! انتخاب کن:", reply_markup=choice_keyboard())
            await send(game["p2"], "دور بعد! انتخاب کن:", reply_markup=choice_keyboard())

# ---------------------------------------------------------
# صف (اصلاح‌شده: خودت رو حریف خودت نکن)
# ---------------------------------------------------------
async def cancel_queue_after_timeout(user_id, chat_id):
    await asyncio.sleep(300)
    for entry in list(match_queue):
        if entry["user_id"] == user_id:
            match_queue.remove(entry)
            await send(chat_id, "⏳ ۵ دقیقه گذشت و حریفی پیدا نشد. از صف خارج شدی.", reply_markup=main_keyboard())
            break

async def try_matchmake(user_id, chat_id):
    if user_id in user_game:
        await send(chat_id, "شما در حال حاضر در یک بازی هستید.")
        return
    for entry in match_queue:
        if entry["user_id"] == user_id:
            await send(chat_id, "شما قبلاً در صف هستید. منتظر بمانید...")
            return

    # حریف: فقط کسی که با خودت یکی نباشه
    opponent = None
    for entry in list(match_queue):
        if entry["user_id"] != user_id:
            opponent = entry
            break

    if opponent:
        match_queue.remove(opponent)
        if opponent.get("task"): opponent["task"].cancel()

        game_id = f"g_{user_id}_{opponent['user_id']}_{random.randint(1000,9999)}"
        active_games[game_id] = {
            "p1": user_id, "p2": opponent["user_id"],
            "score1": 0, "score2": 0,
            "p1_choice": None, "p2_choice": None,
            "is_bot": False,
        }
        user_game[user_id] = game_id
        user_game[opponent["user_id"]] = game_id

        await send(user_id, "🎮 **حریف پیدا شد!** بازی تا ۱۰ امتیاز شروع شد.")
        await send(opponent["user_id"], "🎮 **حریف پیدا شد!** بازی تا ۱۰ امتیاز شروع شد.")
        await send(user_id, "انتخاب کن:", reply_markup=choice_keyboard())
        await send(opponent["user_id"], "انتخاب کن:", reply_markup=choice_keyboard())
    else:
        task = asyncio.create_task(cancel_queue_after_timeout(user_id, chat_id))
        match_queue.append({"user_id": user_id, "chat_id": chat_id, "task": task})
        await send(chat_id, "⏳ در صف انتظار قرار گرفتی. تا ۵ دقیقه منتظر حریف می‌مانی...", reply_markup=main_keyboard())

# ---------------------------------------------------------
# Webhook
# ---------------------------------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = parse_update(await request.json())
        message = update.effective_message

        if update.callback_query:
            cq = update.callback_query
            user_id = cq.from_user.id
            chat_id = cq.message.chat.id
            choice = cq.data
            await client.answer_callback_query(cq.id)
            if user_id in user_game:
                await process_choice(user_id, chat_id, choice, user_game[user_id])
            else:
                await send(chat_id, "بازی فعالی نداری.", reply_markup=main_keyboard())
            return {"ok": True}

        if not message or not message.text:
            return {"ok": True}

        text = message.text.strip()
        user_id = message.from_user.id
        chat_id = message.chat.id

        # /start (با لینک دعوت)
        if text.startswith("/start"):
            parts = text.split(maxsplit=1)
            payload = parts[1] if len(parts) > 1 else None
            if payload and payload in pending_invites:
                invite = pending_invites.pop(payload)
                keyboard = InlineKeyboardMarkup.quick([
                    [("✅ قبول", f"accept_{payload}"), ("❌ رد", f"reject_{payload}")]
                ])
                await send(invite["inviter_chat_id"], f"👤 کاربر {user_id} از لینک دعوت تو استفاده کرد. قبول می‌کنی؟", reply_markup=keyboard)
                await send(chat_id, "درخواست دعوت برای میزبان ارسال شد. منتظر تایید بمان...")
                return {"ok": True}
            await send(chat_id, main_menu(), reply_markup=main_keyboard())
            return {"ok": True}

        # دکمه‌های منو
        if "مسابقه با ربات" in text:
            await start_bot_game(user_id, chat_id)
            return {"ok": True}

        if "بازی با دوست" in text:
            invite_code = f"inv_{user_id}_{random.randint(10000,99999)}"
            pending_invites[invite_code] = {"inviter_id": user_id, "inviter_chat_id": chat_id}
            link = f"https://ble.ir/{BOT_USERNAME}?start={invite_code}"
            await send(chat_id, f"🔗 **لینک دعوت اختصاصی تو:**\n\n`{link}`\n\nاین لینک را برای دوستت بفرست.", reply_markup=main_keyboard())
            return {"ok": True}

        if "جستجوی حریف" in text:
            await try_matchmake(user_id, chat_id)
            return {"ok": True}

        if "لغو" in text:
            for entry in list(match_queue):
                if entry["user_id"] == user_id:
                    match_queue.remove(entry)
                    if entry.get("task"): entry["task"].cancel()
                    await send(chat_id, "از صف خارج شدی.", reply_markup=main_keyboard())
                    return {"ok": True}
            if user_id in user_game:
                game_id = user_game[user_id]
                game = active_games.get(game_id)
                if game:
                    opponent_id = game["p2"] if game["p1"] == user_id else game["p1"]
                    for uid in [game["p1"], game["p2"]]:
                        if uid != "BOT": user_game.pop(uid, None)
                    active_games.pop(game_id, None)
                    if opponent_id != "BOT":
                        await send(opponent_id, "حریف بازی را لغو کرد.", reply_markup=main_keyboard())
                await send(chat_id, "بازی لغو شد.", reply_markup=main_keyboard())
            else:
                await send(chat_id, "بازی یا صف فعالی نداری.", reply_markup=main_keyboard())
            return {"ok": True}

        await send(chat_id, "لطفاً از دکمه‌های منوی زیر استفاده کن.", reply_markup=main_keyboard())
        return {"ok": True}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"ok": True}

@app.get("/")
async def health():
    return {"status": "باشه‌داداش"}
