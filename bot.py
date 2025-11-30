
import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from groq import Groq

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация Groq клиента
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Состояния разговора
AGE, INTERESTS, TEACHER_STYLE, LEARNING = range(4)

# Хранилище пользователей
user_profiles = {}

def create_learning_keyboard():
    """Клавиатура для режима обучения"""
    return ReplyKeyboardMarkup([
        ["🔄 Новый вопрос", "⚙️ Изменить настройки"],
        ["📊 Мой профиль", "🚪 Выход"]
    ], resize_keyboard=True)

def create_personalized_prompt(user_profile, question):
    """Создаёт персонализированный промпт для ИИ"""
    
    age = user_profile["age"]
    interests = user_profile["interests"]
    teacher_style = user_profile["teacher_style"]
    
    # Определяем уровень сложности по возрасту
    if age <= 10:
        complexity = "очень простыми словами, как для ребёнка"
        examples = "игрушки, мультики, игры"
    elif age <= 15:
        complexity = "понятным языком с примерами из жизни"
        examples = "школа, друзья, хобби"
    else:
        complexity = "более глубоко, но доступно"
        examples = "реальные жизненные ситуации"
    
    # Стили преподавания
    styles = {
        "😊 Добрый наставник": "Ты добрый и поддерживающий учитель. Хвали ученика, подбадривай. Говори: 'Молодец!', 'Отлично получается!', 'Я верю в тебя!'",
        "💪 Строгий тренер": "Ты строгий но справедливый тренер. Требуй концентрации, давай чёткие инструкции. Говори: 'Соберись!', 'Фокусируйся!', 'Ты можешь лучше!'",
        "😎 Мемный друг": "Ты крутой друг который объясняет через мемы и шутки. Используй современный сленг, эмодзи. Будь веселым и неформальным.",
        "🥋 Мудрый сенсей": "Ты мудрый сенсей который учит через притчи и аналогии. Говори мудро, спокойно. Используй восточную философию.",
        "🔥 Мотивационный коуч": "Ты энергичный коуч который вдохновляет. Используй мотивационные фразы, ставь цели, показывай прогресс."
    }
    
    # Примеры по интересам
    interest_examples = {
        "⚽ Спорт": "Объясняй через спортивные аналогии: футбол, баскетбол, бег, соревнования.",
        "🎮 Игры": "Используй геймерские аналогии: левел-ап, квесты, боссы, прокачка навыков.",
        "🎬 Фильмы/Аниме": "Проводи параллели с фильмами и аниме, используй примеры из популярных сюжетов.",
        "🚗 Машины": "Объясняй через автомобильные аналогии: двигатель, скорость, турбо, гоночные трассы.",
        "💻 Технологии": "Используй IT-аналогии: процессоры, алгоритмы, баги, апгрейды.",
        "🎨 Искусство": "Проводи параллели с искусством: картины, музыка, творчество, воображение.",
        "🎵 Музыка": "Объясняй через музыкальные аналогии: ритм, гармония, ноты, композиции.",
        "📚 Книги": "Используй литературные примеры, цитаты из книг, аналогии с сюжетами."
    }
    
    style_instruction = styles.get(teacher_style, styles["😊 Добрый наставник"])
    interest_instruction = interest_examples.get(interests, "Используй понятные примеры из повседневной жизни.")
    
    prompt = f"""Ты - AIQYN, персональный ИИ-учитель нового поколения. Твоя задача - НЕ давать готовые ответы, а учить мыслить и понимать.

ПРОФИЛЬ УЧЕНИКА:
- Возраст: {age} лет
- Интересы: {interests}
- Стиль учителя: {teacher_style}

ТВОИ ИНСТРУКЦИИ:
1. {style_instruction}
2. {interest_instruction}
3. ОБЪЯСНЯЙ {complexity}
4. Используй примеры из: {examples}

ГЛАВНЫЕ ПРАВИЛА:
❌ НЕ ДАВАЙ готовые ответы
❌ НЕ надо огромный тексты писать, все коротко и понятно. Чтобы читатель не переутомлялся.
✅ Объясняй все простым и понятным языком
✅ ЗАДАВАЙ наводящие вопросы (метод Сократа)
✅ ОБЪЯСНЯЙ через то, что интересно ученику
✅ ДЕЛАЙ объяснение интерактивным и интересным
✅ ПРОВЕРЯЙ понимание (1-2 вопроса в конце)
✅ ХВАЛИ и мотивируй

ВОПРОС УЧЕНИКА: {question}

ТВОЙ ПЕРСОНАЛИЗИРОВАННЫЙ ОТВЕТ:"""
    
    return prompt

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало разговора - сбор информации о пользователе"""
    user_id = update.effective_user.id
    user_profiles[user_id] = {}
    
    await update.message.reply_text(
        "🌟 Добро пожаловать в AIQYN LEARN!\n\n"
        "Я - ИИ-учитель нового поколения. Я научу тебя понимать, а не просто дам ответы!\n\n"
        "Для начала расскажи о себе:\nСколько тебе лет? (напиши число)",
        reply_markup=ReplyKeyboardRemove()
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем возраст пользователя"""
    user_id = update.effective_user.id
    
    # Проверяем, не хочет ли пользователь выйти или начать заново
    if update.message.text in ["/start", "🚪 Выход", "🔄 Начать заново"]:
        return await start(update, context)
    
    try:
        age = int(update.message.text)
        if age < 6 or age > 100:
            await update.message.reply_text("Пожалуйста, введи реальный возраст (6-100)")
            return AGE
        
        user_profiles[user_id]["age"] = age
        
        # Клавиатура для интересов
        interests_keyboard = [
            ["⚽ Спорт", "🎮 Игры"],
            ["🎬 Фильмы/Аниме", "🚗 Машины"],
            ["💻 Технологии", "🎨 Искусство"],
            ["🎵 Музыка", "📚 Книги"],
            ["🔄 Начать заново"]
        ]
        
        await update.message.reply_text(
            f"Отлично! Тебе {age} лет.\n\n"
            "Что тебе интересно в жизни?\n"
            "Я буду объяснять через твои увлечения!",
            reply_markup=ReplyKeyboardMarkup(interests_keyboard, one_time_keyboard=True)
        )
        return INTERESTS
    except ValueError:
        await update.message.reply_text("Пожалуйста, введи возраст числом (например: 15)")
        return AGE

async def get_interests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем интересы"""
    user_id = update.effective_user.id
    
    # Проверяем, не хочет ли пользователь выйти или начать заново
    if update.message.text in ["/start", "🚪 Выход", "🔄 Начать заново"]:
        return await start(update, context)
    
    user_profiles[user_id]["interests"] = update.message.text
    
    # Клавиатура для стиля учителя
    style_keyboard = [
        ["😊 Добрый наставник", "💪 Строгий тренер"],
        ["😎 Мемный друг", "🥋 Мудрый сенсей"],
        ["🔥 Мотивационный коуч"],
        ["🔄 Начать заново"]
    ]
    
    await update.message.reply_text(
        "Круто! Теперь выбери стиль учителя:\n\n"
        "😊 Добрый наставник - поддержка и забота\n"
        "💪 Строгий тренер - дисциплина и результат\n"  
        "😎 Мемный друг - весело и по-современному\n"
        "🥋 Мудрый сенсей - философия и глубина\n"
        "🔥 Мотивационный коуч - энергия и цели",
        reply_markup=ReplyKeyboardMarkup(style_keyboard, one_time_keyboard=True)
    )
    return TEACHER_STYLE

async def get_teacher_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получаем стиль учителя и начинаем обучение"""
    user_id = update.effective_user.id
    
    # Проверяем, не хочет ли пользователь выйти или начать заново
    if update.message.text in ["/start", "🚪 Выход", "🔄 Начать заново"]:
        return await start(update, context)
    
    user_profiles[user_id]["teacher_style"] = update.message.text
    
    profile = user_profiles[user_id]
    
    await update.message.reply_text(
        f"🎉 Готово! Настраиваю обучение под тебя:\n\n"
        f"👤 Возраст: {profile['age']} лет\n"
        f"❤️ Интересы: {profile['interests']}\n"
        f"🎭 Стиль: {profile['teacher_style']}\n\n"
        f"Теперь задавай любой вопрос! Я помогу разобраться в:\n"
        f"• Математике • Физике • Химии • Биологии\n"
        f"• Истории • Программировании • И многом другом!\n\n"
        f"💡 Примеры вопросов:\n"
        f"• Объясни теорему Пифагора\n"
        f"• Что такое фотосинтез?\n" 
        f"• Как работает электричество?\n\n"
        f"Используй кнопки ниже для управления 👇",
        reply_markup=create_learning_keyboard()
    )
    return LEARNING

async def handle_learning(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вопросов пользователя с персонализацией"""
    user_id = update.effective_user.id
    user_message = update.message.text
    
    # Обработка команд управления
    if user_message == "⚙️ Изменить настройки":
        return await start(update, context)
    
    elif user_message == "📊 Мой профиль":
        if user_id in user_profiles:
            profile = user_profiles[user_id]
            await update.message.reply_text(
                f"📊 Твой профиль:\n\n"
                f"👤 Возраст: {profile['age']} лет\n"
                f"❤️ Интересы: {profile['interests']}\n"
                f"🎭 Стиль: {profile['teacher_style']}\n\n"
                f"Хочешь изменить настройки? Нажми '⚙️ Изменить настройки'",
                reply_markup=create_learning_keyboard()
            )
        else:
            await update.message.reply_text(
                "Профиль не найден. Давай создадим новый! /start",
                reply_markup=create_learning_keyboard()
            )
        return LEARNING
    
    elif user_message == "🔄 Новый вопрос":
        await update.message.reply_text(
            "Отлично! Задавай новый вопрос! 🚀\n\n"
            "Могу объяснить:\n• Математику • Физику • Химию\n• Биологию • Историю • Программирование\n• И многое другое!",
            reply_markup=create_learning_keyboard()
        )
        return LEARNING
    
    elif user_message in ["/start", "🚪 Выход"]:
        await update.message.reply_text(
            "До встречи! Если захочешь учиться снова - напиши /start",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Если это обычный вопрос
    if user_id not in user_profiles:
        await update.message.reply_text(
            "Давай сначала познакомимся! Напиши /start",
            reply_markup=create_learning_keyboard()
        )
        return LEARNING
    
    await update.message.reply_chat_action("typing")
    
    try:
        user_profile = user_profiles[user_id]
        prompt = create_personalized_prompt(user_profile, user_message)
        
        # Получаем ответ от ИИ
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800
        )
        
        answer = response.choices[0].message.content
        
        await update.message.reply_text(answer, reply_markup=create_learning_keyboard())
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            "Упс! Что-то пошло не так. Попробуй ещё раз!",
            reply_markup=create_learning_keyboard()
        )
    
    return LEARNING

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена разговора"""
    await update.message.reply_text(
        "До встречи! Если захочешь учиться снова - напиши /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда помощи"""
    await update.message.reply_text(
        "🤖 AIQYN LEARN - Помощь\n\n"
        "Доступные команды:\n"
        "/start - Начать/перезапустить бота\n"
        "/help - Показать эту справку\n"
        "/profile - Показать мой профиль\n\n"
        "Во время обучения используй кнопки:\n"
        "🔄 Новый вопрос - задать другой вопрос\n"
        "⚙️ Изменить настройки - изменить профиль\n"
        "📊 Мой профиль - посмотреть настройки\n"
        "🚪 Выход - завершить сессию",
        reply_markup=create_learning_keyboard() if update.effective_user.id in user_profiles else ReplyKeyboardRemove()
    )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда показа профиля"""
    user_id = update.effective_user.id
    if user_id in user_profiles:
        profile = user_profiles[user_id]
        await update.message.reply_text(
            f"📊 Твой профиль:\n\n"
            f"👤 Возраст: {profile['age']} лет\n"
            f"❤️ Интересы: {profile['interests']}\n"
            f"🎭 Стиль: {profile['teacher_style']}",
            reply_markup=create_learning_keyboard()
        )
    else:
        await update.message.reply_text(
            "Профиль не найден. Напиши /start чтобы создать профиль!",
            reply_markup=ReplyKeyboardRemove()
        )

def main():
    """Запуск бота"""
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    application = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            INTERESTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_interests)],
            TEACHER_STYLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_teacher_style)],
            LEARNING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_learning)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
            CommandHandler("help", help_command),
            CommandHandler("profile", profile_command)
        ]
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    
    application.run_polling()

if __name__ == "__main__":
    main()
