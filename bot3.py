import logging
from telegram import (
    Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
)
import random

# ----------------- ЛОГИ -----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------- КРАСИВЫЕ КНОПКИ -----------------
main_menu = ReplyKeyboardMarkup(
    [
        ["🧘 Медитация", "🌬 Дыхание"],
        ["⚡ SOS-помощь", "🧩 Техники заземления"],
        ["📒 Дневник эмоций", "😊 Трекер настроения"],
        ["📚 Советы перед экзаменом"],
    ],
    resize_keyboard=True
)

mood_keyboard = ReplyKeyboardMarkup(
    [
        ["😊 Хорошо", "😐 Нормально", "😟 Плохо"],
        ["😭 Очень плохо"],
        ["⬅ Назад в меню"]
    ],
    resize_keyboard=True
)

# ----------------- ТЕКСТЫ -----------------
INTRO = (
    "Привет! ✨\n\n"
    "Я — *АнтиПаника*, твой карманный психолог 🤍\n"
    "Помогу успокоиться, собраться перед экзаменом и вернуть контроль.\n\n"
    "Выбери действие ниже 👇"
)

BREATHING = (
    "🌬 *Дыхательная техника 4–6*\n\n"
    "Вдох — 4 секунды\n"
    "Выдох — 6 секунд\n"
    "Повтори 6 раз.\n\n"
    "Хочешь интерактивную версию?"
)

GROUNDING = (
    "🧩 *Техника заземления 5-4-3-2-1*\n\n"
    "Посмотри вокруг и назови:\n"
    "• 5 предметов, которые ты видишь 👀\n"
    "• 4 предмета, которые можешь потрогать ✋\n"
    "• 3 звука, которые слышишь 👂\n"
    "• 2 запаха, которые чувствуешь 👃\n"
    "• 1 вкус, который ощущаешь 👅\n\n"
    "Это помогает вернуть мозг в реальность и снизить тревогу."
)

EXAM_TIPS = (
    "📚 *СОВЕТЫ ПЕРЕД ЭКЗАМЕНОМ*:\n\n"
    "✔ Сделай 3 глубоких вдоха — дай мозгу кислород\n"
    "✔ Пробеги глазами по конспекту, не зубри\n"
    "✔ Выпей воды — это снизит кортизол\n"
    "✔ Помни: ты знаешь больше, чем кажется 💪\n\n"
    "Хочешь получить мотивацию? 😉"
)

SOS_TEXT = (
    "⚡ *SOS-режим*: мгновенное снижение паники.\n\n"
    "1️⃣ Сделай ОДИН глубокий вдох — медленный выдох\n"
    "2️⃣ Посмотри по сторонам: ты в безопасности\n"
    "3️⃣ Положи ладонь на грудь и скажи:\n"
    "   «Я в безопасности. Паника пройдёт». 🤍\n\n"
    "Готов продолжить работу?"
)

MEDITATIONS = [
    "🧘 *Медитация: 60 секунд тишины*\n\nСядь ровно. Закрой глаза. Просто дыши.",
    "🌊 Представь: ты стоишь у моря, слушаешь шум волн…",
    "🔥 Визуализируй: внутри тебя маленькое теплое пламя, оно успокаивает тело."
]

MOTIVATION = [
    "✨ Ты справишься.",
    "💪 Ты сильнее, чем твоя тревога.",
    "🔥 Ты уже сделал(-а) больше, чем думаешь.",
    "🌱 Ошибки — не провал. Они — путь.",
]

# ----------------- КОМАНДЫ -----------------
def start(update: Update, context: CallbackContext):
    update.message.reply_text(INTRO, reply_markup=main_menu, parse_mode="Markdown")


def handle_menu(update: Update, context: CallbackContext):
    text = update.message.text

    if text == "🧘 Медитация":
        update.message.reply_text(random.choice(MEDITATIONS), parse_mode="Markdown")

    elif text == "🌬 Дыхание":
        breathing_buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶ Начать упражнение", callback_data="breath_start")]
        ])
        update.message.reply_text(BREATHING, reply_markup=breathing_buttons, parse_mode="Markdown")

    elif text == "⚡ SOS-помощь":
        update.message.reply_text(SOS_TEXT, parse_mode="Markdown")

    elif text == "🧩 Техники заземления":
        update.message.reply_text(GROUNDING, parse_mode="Markdown")

    elif text == "📚 Советы перед экзаменом":
        motivation_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚡ Дай мотивацию!", callback_data="motivate")]
        ])
        update.message.reply_text(EXAM_TIPS, reply_markup=motivation_button, parse_mode="Markdown")

    elif text == "📒 Дневник эмоций":
        update.message.reply_text("Как ты себя чувствуешь сегодня? 💭", reply_markup=mood_keyboard)

    elif text == "😊 Трекер настроения":
        update.message.reply_text("Выбери настроение:", reply_markup=mood_keyboard)

    elif text == "⬅ Назад в меню":
        update.message.reply_text("Главное меню:", reply_markup=main_menu)


def save_mood(update: Update, context: CallbackContext):
    mood = update.message.text
    if mood in ["😊 Хорошо", "😐 Нормально", "😟 Плохо", "😭 Очень плохо"]:
        update.message.reply_text(f"Записано: *{mood}*\nТы молодец, что следишь за собой 🤍",
                                  reply_markup=main_menu, parse_mode="Markdown")


# ----------------- INLINE КНОПКИ -----------------
def inline_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "breath_start":
        query.edit_message_text(
            "🌬 *Начинаем дыхание:*\n\n"
            "Вдох — 4 секунды…\n"
            "Выдох — 6 секунд…\n"
            "Повтори 6 раз 🕊",
            parse_mode="Markdown"
        )

    elif query.data == "motivate":
        query.edit_message_text(
            f"⚡ *Мотивация:* {random.choice(MOTIVATION)}", parse_mode="Markdown"
        )


# ----------------- РАН -----------------
def main():
    updater = Updater("YOUR_TOKEN")

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(inline_handler))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, save_mood))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_menu))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()