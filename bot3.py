import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    CallbackContext
)

import sqlite3
import random
import datetime

# ---------------- ЛОГИ ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_TOKEN"

# ---------------- БАЗА ДАННЫХ ----------------

def init_db():
    conn = sqlite3.connect("emotions.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS mood (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, mood TEXT, date TEXT)"
    )
    conn.commit()
    conn.close()

def save_mood(user_id, mood):
    conn = sqlite3.connect("emotions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO mood (user_id, mood, date) VALUES (?, ?, ?)",
        (user_id, mood, str(datetime.date.today()))
    )
    conn.commit()
    conn.close()

# ---------------- МЕНЮ ----------------

main_menu = ReplyKeyboardMarkup(
    [
        ["🧘 Медитация", "🌬 Дыхание"],
        ["🧩 Grounding", "⚡ SOS"],
        ["📒 Дневник", "😊 Настроение"],
        ["📚 Экзамен", "📝 GAD-7"],
        ["📬 Письмо себе", "⏰ Напоминания"],
    ],
    resize_keyboard=True
)

mood_menu = ReplyKeyboardMarkup(
    [
        ["😊 Хорошо", "😐 Так себе", "😟 Плохо", "😭 Очень плохо"],
        ["⬅ Назад"]
    ],
    resize_keyboard=True
)

# ---------------- ТЕКСТЫ ----------------

BREATHING = (
    "🌬 *Техника дыхания 4–6*\n\n"
    "Вдох на 4 секунды\n"
    "Выдох на 6 секунд\n"
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
    "🔥 Представь тёплое мягкое пламя внутри груди."
]

MOTIVATION = [
    "✨ Ты справишься.",
    "💪 Ты сильнее, чем твоя тревога.",
    "🔥 Ты — не свои страхи.",
    "🌱 Сегодня ты уже сделал шаг вперёд."
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

# ---------------- GAD-7 ----------------

GAD7_QUESTIONS = [
    "1. Чувствовали ли вы нервозность, тревожность или на взводе?",
    "2. Не могли остановить или контролировать беспокойство?",
    "3. Часто беспокоились по разным поводам?",
    "4. Было ли трудно расслабиться?",
    "5. Были ли настолько беспокойны, что трудно сидеть на месте?",
    "6. Легко ли вы раздражались или расстраивались?",
    "7. Чувствовали ли страх, будто что-то ужасное может случиться?"
]

def gad7_start(update: Update, context: CallbackContext):
    context.user_data["gad7"] = {"index": 0, "score": 0}
    update.message.reply_text(
        "📝 *Тест GAD-7: определение уровня тревожности*\n\n"
        "Ответь оценкой от 0 до 3:\n"
        "0 — никогда\n1 — несколько дней\n2 — более половины дней\n3 — почти каждый день",
        parse_mode="Markdown"
    )
    update.message.reply_text(GAD7_QUESTIONS[0])

def gad7_process(update: Update, context: CallbackContext):
    if "gad7" not in context.user_data:
        return False

    try:
        answer = int(update.message.text)
        if answer not in [0, 1, 2, 3]:
            raise ValueError
    except:
        update.message.reply_text("Ответ должен быть числом 0–3.")
        return True

    context.user_data["gad7"]["score"] += answer
    context.user_data["gad7"]["index"] += 1

    idx = context.user_data["gad7"]["index"]

    if idx < 7:
        update.message.reply_text(GAD7_QUESTIONS[idx])
        return True
    else:
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

        update.message.reply_text(
            f"Твой результат: *{score}* баллов.\n{level} 🤍",
            parse_mode="Markdown"
        )
        return True

# ---------------- НАПОМИНАНИЯ ----------------

def reminder_handler(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    if not text.startswith("напомнить"):
        return False

    # формат: "напомнить вода 60"
    parts = text.split()
    if len(parts) != 3:
        update.message.reply_text("Формат: напомнить <что> <минуты>")
        return True

    what = parts[1]
    try:
        minutes = int(parts[2])
    except:
        update.message.reply_text("Минуты должны быть числом.")
        return True

    context.job_queue.run_once(
        lambda c: update.message.reply_text(f"⏰ Напоминание: {what}!"),
        minutes * 60
    )

    update.message.reply_text(f"Ок! Напомню через {minutes} минут 🤍")
    return True

# ---------------- ПИСЬМО СЕБЕ ----------------

def save_letter(update: Update, context: CallbackContext):
    if context.user_data.get("letter_mode"):
        with open("letter.txt", "w", encoding="utf-8") as f:
            f.write(update.message.text)
        update.message.reply_text("Письмо сохранено! Отправлю через 7 дней 💌")
        context.user_data["letter_mode"] = False
        return True
    return False

# ---------------- ОБРАБОТЧИК МЕНЮ ----------------

def menu(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "🌬 Дыхание":
        update.message.reply_text(BREATHING, parse_mode="Markdown")

    elif text == "🧘 Медитация":
        update.message.reply_text(random.choice(MEDITATIONS), parse_mode="Markdown")

    elif text == "🧩 Grounding":
        update.message.reply_text(GROUNDING, parse_mode="Markdown")

    elif text == "⚡ SOS":
        update.message.reply_text(SOS_TEXT, parse_mode="Markdown")

    elif text == "📒 Дневник" or text == "😊 Настроение":
        update.message.reply_text("Как ты себя чувствуешь?", reply_markup=mood_menu)

    elif text == "⬅ Назад":
        update.message.reply_text("Меню:", reply_markup=main_menu)

    elif text in ["😊 Хорошо", "😐 Так себе", "😟 Плохо", "😭 Очень плохо"]:
        save_mood(update.message.from_user.id, text)
        update.message.reply_text("Записал 🤍", reply_markup=main_menu)

    elif text == "📚 Экзамен":
        update.message.reply_text(
            EXAM_TIPS,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⚡ Мотивация!", callback_data="motivate")]]
            ),
            parse_mode="Markdown"
        )

    elif text == "📝 GAD-7":
        gad7_start(update, context)

    elif text == "⏰ Напоминания":
        update.message.reply_text(
            "Напиши: *напомнить <что> <минуты>*\n\nПример: `напомнить вода 30`",
            parse_mode="Markdown"
        )

    elif text == "📬 Письмо себе":
        update.message.reply_text("Напиши своё письмо, я сохраню его 💌")
        context.user_data["letter_mode"] = True

# ---------------- INLINE ----------------

def inline_handler(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()

    if q.data == "motivate":
        q.edit_message_text("⚡ " + random.choice(MOTIVATION))

# ---------------- ГЛАВНЫЙ ОБРАБОТЧИК ----------------

def text_router(update: Update, context: CallbackContext):

    # GAD-7
    if gad7_process(update, context):
        return

    # Reminder
    if reminder_handler(update, context):
        return

    # Письмо
    if save_letter(update, context):
        return

    # Меню
    menu(update, context)

# ---------------- MAIN ----------------

def main():
    init_db()

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Привет!", reply_markup=main_menu)))
    dp.add_handler(CallbackQueryHandler(inline_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_router))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()