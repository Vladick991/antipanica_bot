import logging
import random
import datetime
import sqlite3

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ------------------ LOGGING ------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8473801558:AAFmRkmPU8vJmcmQET5bATmD_NVwc9LWi2Q"


# ------------------ DATABASE ------------------

def init_db():
    conn = sqlite3.connect("emotions.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS mood (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            mood TEXT,
            date TEXT
        )
        """
    )
    conn.commit()
    conn.close()


async def save_mood(user_id, mood):
    conn = sqlite3.connect("emotions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO mood (user_id, mood, date) VALUES (?, ?, ?)",
        (user_id, mood, str(datetime.date.today())),
    )
    conn.commit()
    conn.close()


# ------------------ KEYBOARDS ------------------

main_menu = ReplyKeyboardMarkup(
    [
        ["🧘 Медитация", "🌬 Дыхание"],
        ["🧩 Grounding", "⚡ SOS"],
        ["📒 Дневник", "😊 Настроение"],
        ["📚 Экзамен", "📝 GAD-7"],
        ["📬 Письмо себе", "⏰ Напоминания"],
    ],
    resize_keyboard=True,
)

mood_menu = ReplyKeyboardMarkup(
    [
        ["😊 Хорошо", "😐 Так себе", "😟 Плохо", "😭 Очень плохо"],
        ["⬅ Назад"],
    ],
    resize_keyboard=True,
)


# ------------------ TEXT CONTENT ------------------

BREATHING = (
    "🌬 *Техника дыхания 4–6*\n\n"
    "Вдох — 4 секунды\n"
    "Выдох — 6 секунд\n"
    "Повтори 6 раз 🕊"
)

GROUNDING = (
    "🧩 *Техника заземления 5-4-3-2-1*\n\n"
    "Назови:\n"
    "5 предметов, которые видишь 👀\n"
    "4 предмета, которые можешь потрогать ✋\n"
    "3 звука вокруг 👂\n"
    "2 запаха 👃\n"
    "1 вкус 👅\n\n"
    "Это помогает снизить тревогу и вернуться в тело."
)

MEDITATIONS = [
    "🧘 *Медитация: 60 секунд тишины*\nЗакрой глаза. Просто дыши.",
    "🌊 Представь море. Волна накатывает — волна уходит…",
    "🔥 Представь тёплое мягкое пламя внутри груди.",
]

MOTIVATION = [
    "✨ Ты справишься.",
    "💪 Ты сильнее, чем твоя тревога.",
    "🔥 Ты — не свои страхи.",
    "🌱 Сегодня ты уже сделал шаг вперёд.",
]

EXAM_TIPS = (
    "📚 *Советы перед экзаменом:*\n\n"
    "✔ Сделай 3 глубоких вдоха\n"
    "✔ Посмотри конспект, но не зубри\n"
    "✔ Выпей воды — это снижает стресс\n"
    "✔ Ты знаешь больше, чем кажется!\n\n"
)

SOS_TEXT = (
    "⚡ *SOS техника:*\n\n"
    "1️⃣ Глубокий вдох\n"
    "2️⃣ Медленный выдох\n"
    "3️⃣ Скажи: *«Я в безопасности»*\n"
    "4️⃣ Почувствуй стопы и опору\n"
    "5️⃣ Посмотри по сторонам: всё ок\n\n"
    "Ты справишься 🤍"
)

# ------------------ GAD-7 ------------------

GAD7_QUESTIONS = [
    "1. Чувствовали ли вы нервозность, тревожность или на взводе?",
    "2. Не могли остановить или контролировать беспокойство?",
    "3. Часто беспокоились по разным поводам?",
    "4. Было ли трудно расслабиться?",
    "5. Были ли настолько беспокойны, что трудно сидеть на месте?",
    "6. Легко ли вы раздражались или расстраивались?",
    "7. Чувствовали ли страх, будто что-то ужасное может случиться?",
]


async def gad7_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gad7"] = {"index": 0, "score": 0}

    await update.message.reply_text(
        "📝 *Тест GAD-7: уровень тревожности*\n\n"
        "Ответь оценкой 0–3:\n"
        "0 — никогда\n1 — иногда\n2 — часто\n3 — почти всегда",
        parse_mode="Markdown",
    )
    await update.message.reply_text(GAD7_QUESTIONS[0])


async def gad7_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "gad7" not in context.user_data:
        return False

    try:
        value = int(update.message.text)
        if value not in [0, 1, 2, 3]:
            raise ValueError
    except:
        await update.message.reply_text("Ответ должен быть 0–3.")
        return True

    context.user_data["gad7"]["score"] += value
    context.user_data["gad7"]["index"] += 1
    idx = context.user_data["gad7"]["index"]

    if idx < 7:
        await update.message.reply_text(GAD7_QUESTIONS[idx])
        return True

    score = context.user_data["gad7"]["score"]
    del context.user_data["gad7"]

    if score <= 4:
        level = "Минимальная тревожность"
    elif score <= 9:
        level = "Лёгкая тревожность"
    elif score <= 14:
        level = "Средняя тревожность"
    else:
        level = "Тяжёлая тревожность"

    await update.message.reply_text(
        f"Твой результат: *{score}* баллов.\n{level} 🤍",
        parse_mode="Markdown",
    )
    return True


# ------------------ REMINDERS ------------------

async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    what = context.job.data["what"]
    await context.bot.send_message(chat_id, f"⏰ Напоминание: {what}!")


async def process_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if not text.startswith("напомнить"):
        return False

    parts = text.split()
    if len(parts) != 3:
        await update.message.reply_text("Формат: напомнить <что> <минуты>")
        return True

    what = parts[1]
    try:
        minutes = int(parts[2])
    except:
        await update.message.reply_text("Минуты должны быть числом.")
        return True

    context.job_queue.run_once(
        reminder_job,
        when=minutes * 60,
        data={"chat_id": update.message.chat_id, "what": what},
    )

    await update.message.reply_text(f"Ок! Напомню через {minutes} минут 🤍")
    return True


# ------------------ LETTER TO SELF ------------------

async def process_letter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("letter_mode"):
        return False

    with open("letter.txt", "w", encoding="utf-8") as f:
        f.write(update.message.text)

    await update.message.reply_text("Письмо сохранено! Отправлю через 7 дней 💌")
    context.user_data["letter_mode"] = False
    return True


# ------------------ MENU HANDLER ------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🌬 Дыхание":
        await update.message.reply_text(BREATHING, parse_mode="Markdown")

    elif text == "🧘 Медитация":
        await update.message.reply_text(random.choice(MEDITATIONS), parse_mode="Markdown")

    elif text == "🧩 Grounding":
        await update.message.reply_text(GROUNDING, parse_mode="Markdown")

    elif text == "⚡ SOS":
        await update.message.reply_text(SOS_TEXT, parse_mode="Markdown")

    elif text == "📒 Дневник" or text == "😊 Настроение":
        await update.message.reply_text("Как ты себя чувствуешь?", reply_markup=mood_menu)

    elif text == "⬅ Назад":
        await update.message.reply_text("Меню:", reply_markup=main_menu)

    elif text in ["😊 Хорошо", "😐 Так себе", "😟 Плохо", "😭 Очень плохо"]:
        await save_mood(update.message.from_user.id, text)
        await update.message.reply_text("Записал 🤍", reply_markup=main_menu)

    elif text == "📚 Экзамен":
        await update.message.reply_text(
            EXAM_TIPS,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚡ Мотивация!", callback_data="motivate")]]
            ),
            parse_mode="Markdown",
        )

    elif text == "📝 GAD-7":
        await gad7_start(update, context)

    elif text == "⏰ Напоминания":
        await update.message.reply_text(
            "Напиши: *напомнить <что> <минуты>*\n\nПример: `напомнить вода 30`",
            parse_mode="Markdown",
        )

    elif text == "📬 Письмо себе":
        await update.message.reply_text("Напиши своё письмо 💌")
        context.user_data["letter_mode"] = True


# ------------------ INLINE BUTTONS ------------------

async def inline_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "motivate":
        await query.edit_message_text("⚡ " + random.choice(MOTIVATION))


# ------------------ TEXT ROUTER ------------------

async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # GAD-7
    if await gad7_process(update, context):
        return

    # Reminders
    if await process_reminder(update, context):
        return

    # Letter to self
    if await process_letter(update, context):
        return

    # Menu
    await menu(update, context)


# ------------------ START COMMAND ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я АнтиПаника 🤍", reply_markup=main_menu)


# ------------------ MAIN ------------------

def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(inline_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))

    app.run_polling()


if __name__ == "__main__":
    main()