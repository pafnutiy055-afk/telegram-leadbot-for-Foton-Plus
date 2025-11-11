import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage

# === Твой токен ===
bot = Bot(token="8256043915:AAG9duy42NtybMUsHgOtnbYVv2leGvWsFzA")
dp = Dispatcher(storage=MemoryStorage())

ADMIN_CHAT_ID = -1003108483615  # 🔹 сюда вставь ID чата/группы, куда будут приходить заявки
CHANNEL_USERNAME = "@FOTON_PLUS"  # <-- канал, на который должна быть подписка


# === Машина состояний ===
class Quiz(StatesGroup):
    name = State()
    age = State()
    experience = State()
    goal = State()
    phone = State()
    ready = State()


user_last_message = {}


# === Проверка подписки и старт ===
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
    except Exception:
        await message.answer("❌ Не могу проверить подписку. Попробуйте позже.")
        return

    if member.status in ["left", "kicked"]:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/FOTON_PLUS")],
                [InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")]
            ]
        )
        await message.answer(
            "🚀 Чтобы начать, подпишись на наш канал, где делимся идеями и кейсами по маркетингу 👇",
            reply_markup=keyboard
        )
        return

    # Если подписан — начинаем квиз
    await message.answer(
        "👋 Привет! Этот бот поможет подобрать для тебя идеальный путь в рекламе и маркетинге.\n\n"
        "Для начала — как тебя зовут?"
    )
    await state.set_state(Quiz.name)


# === Проверка кнопки "Проверить подписку" ===
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_subscription(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
    except Exception:
        await callback.message.answer("❌ Не могу проверить подписку. Попробуйте позже.")
        return

    if member.status in ["member", "administrator", "creator"]:
        await callback.message.answer("Отлично! 🎯 Ты подписан.\n\nТеперь расскажи, как тебя зовут?")
        await state.set_state(Quiz.name)
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Подписаться на канал", url="https://t.me/FOTON_PLUS")],
                [InlineKeyboardButton(text="✅ Проверить снова", callback_data="check_sub")]
            ]
        )
        await callback.message.answer(
            "❌ Похоже, ты ещё не подписался.\nПодпишись на канал, чтобы продолжить 👇",
            reply_markup=keyboard
        )


# === Имя ===
@dp.message(Quiz.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Пожалуйста, введи имя чуть подробнее 😊")
        return

    await state.update_data(name=name)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="age_yes")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="age_no")]
        ]
    )

    msg = await message.answer(f"Приятно познакомиться, {name}! 😎\n\nТебе уже есть 18 лет?", reply_markup=keyboard)
    user_last_message[message.from_user.id] = msg.message_id
    await state.set_state(Quiz.age)


# === Возраст ===
@dp.callback_query(lambda c: c.data in ["age_yes", "age_no"])
async def process_age(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "age_no":
        await callback.message.answer("😔 К сожалению, курс доступен только для пользователей старше 18 лет.")
        await state.clear()
        return

    await bot.delete_message(callback.message.chat.id, callback.message.message_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📈 Есть", callback_data="exp_yes")],
            [InlineKeyboardButton(text="🆕 Нет опыта", callback_data="exp_no")]
        ]
    )
    msg = await callback.message.answer("Есть ли у тебя опыт в рекламе или маркетинге?", reply_markup=keyboard)
    user_last_message[callback.from_user.id] = msg.message_id
    await state.set_state(Quiz.experience)


# === Опыт ===
@dp.callback_query(lambda c: c.data in ["exp_yes", "exp_no"])
async def process_experience(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    await state.update_data(experience="Есть" if callback.data == "exp_yes" else "Нет")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Хочу научиться запускать рекламу", callback_data="goal_ads")],
            [InlineKeyboardButton(text="💼 Хочу продвигать свой бизнес", callback_data="goal_biz")],
            [InlineKeyboardButton(text="🎯 Просто хочу разобраться", callback_data="goal_learn")]
        ]
    )
    msg = await callback.message.answer("Какая у тебя главная цель обучения?", reply_markup=keyboard)
    user_last_message[callback.from_user.id] = msg.message_id
    await state.set_state(Quiz.goal)


# === Цель ===
@dp.callback_query(lambda c: c.data.startswith("goal_"))
async def process_goal(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)

    goals = {
        "goal_ads": "Хочу научиться запускать рекламу",
        "goal_biz": "Хочу продвигать свой бизнес",
        "goal_learn": "Просто хочу разобраться"
    }
    await state.update_data(goal=goals[callback.data])

    # Запрос телефона
    contact_btn = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить мой номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.answer("📞 Оставь, пожалуйста, свой номер телефона, чтобы менеджер мог с тобой связаться:", reply_markup=contact_btn)
    await state.set_state(Quiz.phone)


# === Телефон ===
@dp.message(Quiz.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()

    if not phone or len(phone) < 5:
        await message.answer("❌ Введи, пожалуйста, корректный номер телефона.")
        return

    await state.update_data(phone=phone)

    # Убираем клавиатуру
    await message.answer("Спасибо! 🙌", reply_markup=types.ReplyKeyboardRemove())

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Хочу стартовать прямо сегодня", callback_data="ready_yes")],
            [InlineKeyboardButton(text="⏳ Пока не готов", callback_data="ready_no")]
        ]
    )
    msg = await message.answer("Ты готов сделать первый шаг и начать обучение прямо сейчас?", reply_markup=keyboard)
    user_last_message[message.from_user.id] = msg.message_id
    await state.set_state(Quiz.ready)


# === Финал ===
@dp.callback_query(lambda c: c.data in ["ready_yes", "ready_no"])
async def finish_quiz(callback: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback.message.chat.id, callback.message.message_id)
    data = await state.get_data()

    name = data.get("name", "—")
    experience = data.get("experience", "—")
    goal = data.get("goal", "—")
    phone = data.get("phone", "—")
    ready = "Готов начать" if callback.data == "ready_yes" else "Пока не готов"

    # Ссылка на пользователя
    user = callback.from_user
    if user.username:
        user_link = f"https://t.me/{user.username}"
    else:
        user_link = f"tg://user?id={user.id}"

    # Ответ пользователю
    if callback.data == "ready_yes":
        await callback.message.answer(f"🔥 Отлично, {name}! Скоро с тобой свяжется наш менеджер 👩‍💼")
    else:
        await callback.message.answer(f"👌 Хорошо, {name}! Если решишь вернуться — просто напиши /start.")

    # Заявка админу
    summary = (
        f"📩 <b>Новая заявка с квиза</b>\n\n"
        f"👤 Имя: {name}\n"
        f"🧠 Опыт: {experience}\n"
        f"🎯 Цель: {goal}\n"
        f"📞 Телефон: {phone}\n"
        f"🚀 Готовность: {ready}\n"
        f"🔗 Пользователь: <a href=\"{user_link}\">{user.full_name}</a>\n"
        f"🆔 Telegram ID: {user.id}"
    )

    try:
        await bot.send_message(ADMIN_CHAT_ID, summary, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        print(f"Ошибка отправки админу: {e}")

    await state.clear()


# === Запуск ===
async def main():
    print("🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
