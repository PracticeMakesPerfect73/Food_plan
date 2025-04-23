import sqlite3
import datetime
import random
import os
from telegram import InlineKeyboardMarkup
import keyboards

DB_NAME = "foodplan_mvp.db"
IMAGES_FOLDER = "images"
DAILY_FREE_LIMIT = 300


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            daily_recipes_count INTEGER DEFAULT 0,
            last_recipe_date TEXT,
            is_subscribed BOOLEAN DEFAULT FALSE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS liked_recipes (
            user_id INTEGER,
            recipe_id INTEGER,
            PRIMARY KEY (user_id, recipe_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()


def add_or_update_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT last_recipe_date FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if user is None:
        cursor.execute("INSERT INTO users (user_id, daily_recipes_count, last_recipe_date, is_subscribed) VALUES (?, ?, ?, ?)",
                       (user_id, 0, today, False))
    else:
        if user['last_recipe_date'] != today:
            cursor.execute("UPDATE users SET daily_recipes_count = 0, last_recipe_date = ? WHERE user_id = ?", (today, user_id))
        else:
            cursor.execute("UPDATE users SET last_recipe_date = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    conn.close()


def get_user_data(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def increment_daily_recipes_count(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET daily_recipes_count = daily_recipes_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def add_liked_recipe(user_id, recipe_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO liked_recipes (user_id, recipe_id) VALUES (?, ?)", (user_id, recipe_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def get_liked_recipe_ids(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recipe_id FROM liked_recipes WHERE user_id = ?", (user_id,))
    liked_ids = cursor.fetchall()
    conn.close()
    return [row['recipe_id'] for row in liked_ids]


def get_recipes_list(dispatcher):
    return dispatcher.bot_data.get('recipes', [])


def get_random_recipe(dispatcher):
    recipes = get_recipes_list(dispatcher)
    return random.choice(recipes) if recipes else None


def get_recipe_by_id(dispatcher, recipe_id):
    recipes = get_recipes_list(dispatcher)
    try:
        recipe_id = int(recipe_id)
    except (ValueError, TypeError):
        return None

    for recipe in recipes:
        if recipe.get('id') == recipe_id:
            return recipe
    return None


def start_command(update, context):
    user_id = update.effective_user.id
    add_or_update_user(user_id)

    welcome_text = (
        "Привет! Я FoodPlan бот, твой помощник в планировании рациона.\n\n"
        "Я помогу тебе выбрать, что приготовить, составлю список покупок и помогу сэкономить время и деньги!\n\n"
        f"В бесплатной версии тебе доступно {DAILY_FREE_LIMIT} рецепта в день. "
        "Оформи подписку для безлимитного доступа и дополнительных функций!\n\n"
        "Готов начать?"
    )
    reply_markup = keyboards.start_keyboard()
    update.message.reply_text(welcome_text, reply_markup=reply_markup)
    

def get_recipe_action(update, context):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    add_or_update_user(user_id)

    user_data = get_user_data(user_id)
    if not user_data:
        context.bot.send_message(chat_id=user_id, text="Произошла ошибка. Пожалуйста, попробуйте /start снова.")
        return

    if not get_recipes_list(context.dispatcher):
        context.bot.send_message(chat_id=user_id, text="К сожалению, рецепты пока не загружены.")
        return

    if not user_data['is_subscribed'] and user_data['daily_recipes_count'] >= DAILY_FREE_LIMIT:
        reply_markup = keyboards.subscribe_keyboard()
        context.bot.send_message(
            chat_id=user_id,
            text=f"Дневной лимит ({DAILY_FREE_LIMIT}) исчерпан.\nОформите подписку для безлимитного доступа!",
            reply_markup=reply_markup
        )
        return

    recipe = get_random_recipe(context.dispatcher)
    if recipe:
        increment_daily_recipes_count(user_id)
        recipe_id = recipe.get('id')
        name = recipe.get('name', 'Неизвестный рецепт')
        description = recipe.get('description', 'Описание отсутствует.')
        ingredients = recipe.get('ingredients', 'Список продуктов отсутствует.')
        photo_path = recipe.get('photo_path')

        caption = f"*{name}*\n\n{description}"
        reply_markup = keyboards.recipe_keyboard(recipe_id or "placeholder")

        full_photo_path = os.path.join(IMAGES_FOLDER, photo_path.replace(f"{IMAGES_FOLDER}/", "")) if photo_path else None

        if full_photo_path and os.path.exists(full_photo_path):
            with open(full_photo_path, 'rb') as photo_file:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo_file,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        else:
            context.bot.send_message(chat_id=user_id, text=caption, parse_mode='Markdown', reply_markup=reply_markup)


def favorites_command(update, context):
    user_id = update.effective_user.id
    add_or_update_user(user_id)
    liked_recipe_ids = get_liked_recipe_ids(user_id)

    if not liked_recipe_ids:
        response = "У вас пока нет избранных рецептов. Нажмите 'Поставить лайк' под понравившимся рецептом!"
    else:
        liked_names = []
        for recipe_id in liked_recipe_ids:
            recipe = get_recipe_by_id(context.dispatcher, recipe_id)
            name = recipe.get('name', f'Рецепт с ID {recipe_id} (название неизвестно)') if recipe else f'Рецепт с ID {recipe_id} (не найден)'
            liked_names.append(name)
        response = "Ваши избранные рецепты:\n\n" + "\n".join(f"- {name}" for name in liked_names)

    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text=response)


def button_callback_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "get_recipe":
        get_recipe_action(update, context)
        return

    if data == "get_favorites":
        update.effective_user.id = user_id
        favorites_command(update, context)
        return

    if data == "back_to_menu":
        context.bot.send_message(chat_id=user_id, text="Вы вернулись в главное меню:", reply_markup=keyboards.start_keyboard())
        return

    if data.startswith("ingredients_"):
        recipe_id = int(data.split("_")[1])
        recipe = get_recipe_by_id(context.dispatcher, recipe_id)
        if recipe and recipe.get('ingredients'):
            ingredients_text = f"Список продуктов для '{recipe.get('name', 'Неизвестный рецепт')}':\n\n{recipe.get('ingredients')}"
            context.bot.send_message(chat_id=user_id, text=ingredients_text)
        else:
            query.answer("Нет информации о рецепте или списке продуктов.")

    elif data.startswith("like_"):
        recipe_id = int(data.split("_")[1])
        if not get_recipe_by_id(context.dispatcher, recipe_id):
            query.answer("Этот рецепт больше недоступен.")
            return
        added = add_liked_recipe(user_id, recipe_id)
        query.answer("Рецепт добавлен в избранное!" if added else "Этот рецепт уже в вашем избранном!")

    elif data == "subscribe_placeholder":
        context.bot.send_message(chat_id=user_id, text="Раздел подписки в разработке!")

    else:
        query.answer("Неизвестная кнопка.")
