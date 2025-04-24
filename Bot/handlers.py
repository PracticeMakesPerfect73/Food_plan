import sys
import sqlite3
import datetime
import random
import os
from telegram import InlineKeyboardMarkup
import keyboards
from django.db.models import Count # Импортируем Count для случайного выбора рецепта

sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
from FoodBot.models import Recipe

# --- Функции для работы с базой данных SQLite (для пользователей и избранного) ---
# ОСТАВЛЯЕМ если данные пользователей и избранных рецептов пока хранятся в SQLite.
# Для полной интеграции с Django, нужно перенести эту логику в модели Django.

DB_NAME = "foodplan_mvp.db"
IMAGES_FOLDER = "images" # Используется, если изображения хранятся локально и не полностью управляются Django ImageField
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
        if not Recipe.objects.filter(id=recipe_id).exists():
             print(f"Внимание: Попытка поставить лайк несуществующему рецепту с ID {recipe_id}")
             conn.close()
             return False

        cursor.execute("INSERT INTO liked_recipes (user_id, recipe_id) VALUES (?, ?)", (user_id, recipe_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
    except Exception as e:
        print(f"Ошибка при добавлении понравившегося рецепта в SQLite: {e}")
        conn.close()
        return False


def get_liked_recipe_ids(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recipe_id FROM liked_recipes WHERE user_id = ?", (user_id,))
    liked_ids = cursor.fetchall()
    conn.close()
    return [row['recipe_id'] for row in liked_ids]


def get_random_recipe():
    """Получает случайный рецепт из базы данных Django."""
    count = Recipe.objects.aggregate(count=Count('id'))['count']
    if count == 0:
        return None
    random_index = random.randint(0, count - 1)
    return Recipe.objects.all()[random_index]


def get_recipe_by_id(recipe_id):
    """Получает рецепт по ID из базы данных Django."""
    try:
        return Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return None
    except (ValueError, TypeError):
        return None


def start_command(update, context):
    user_id = update.effective_user.id
    add_or_update_user(user_id) # Работает с SQLite DB

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
    add_or_update_user(user_id) # Работает с SQLite DB

    user_data = get_user_data(user_id) # Работает с SQLite DB
    if not user_data:
        context.bot.send_message(chat_id=user_id, text="Произошла ошибка. Пожалуйста, попробуйте /start снова.")
        return

    # Проверка лимита рецептов (работает с SQLite DB)
    if not user_data['is_subscribed'] and user_data['daily_recipes_count'] >= DAILY_FREE_LIMIT:
        reply_markup = keyboards.subscribe_keyboard()
        context.bot.send_message(
            chat_id=user_id,
            text=f"Дневной лимит ({DAILY_FREE_LIMIT}) исчерпан.\nОформите подписку для безлимитного доступа!",
            reply_markup=reply_markup
        )
        return

    # Получаем случайный рецепт из базы данных Django
    recipe = get_random_recipe()

    if recipe:
        increment_daily_recipes_count(user_id) # Работает с SQLite DB
        recipe_id = recipe.id # Используем ID из модели Django
        name = recipe.title # Используем поля модели Django
        description = recipe.description
        photo = recipe.image # Поле image из модели Django

        caption = f"*{name}*\n\n{description}"
        reply_markup = keyboards.recipe_keyboard(recipe_id) # Передаем ID рецепта

        # Обработка изображения из Django ImageField
    if photo and photo.path:
        try:
            with open(photo.path, 'rb') as image_file:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_file
                )
            context.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")
            context.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:
        context.bot.send_message(
            chat_id=user_id,
            text=caption,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )



def favorites_command(update, context):
    user_id = update.effective_user.id
    add_or_update_user(user_id) # Работает с SQLite DB
    liked_recipe_ids = get_liked_recipe_ids(user_id) # Работает с SQLite DB

    if not liked_recipe_ids:
        response = "У вас пока нет избранных рецептов. Нажмите 'Поставить лайк' под понравившимся рецептом!"
    else:
        # Получаем объекты рецептов из Django DB по ID из списка избранных SQLite
        liked_recipes = Recipe.objects.filter(id__in=liked_recipe_ids)
        if not liked_recipes.exists():
             response = "Ваш список избранных пуст или рецепты были удалены."
        else:
            liked_names = [recipe.title for recipe in liked_recipes]
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
        favorites_command(update, context)
        return

    elif data.startswith("like_"):
        try:
            recipe_id = int(data.split("_")[1])
            # Проверяем наличие рецепта в Django DB перед добавлением в избранное SQLite
            if not get_recipe_by_id(recipe_id):
                 query.answer("Этот рецепт больше недоступен.")
                 return

            added = add_liked_recipe(user_id, recipe_id) # Добавляет в SQLite DB
            query.answer("Рецепт добавлен в избранное!" if added else "Этот рецепт уже в вашем избранном!")

        except (ValueError, IndexError):
            query.answer("Ошибка при обработке запроса лайка.")


    elif data == "subscribe_placeholder":
        context.bot.send_message(chat_id=user_id, text="Раздел подписки в разработке!")

    else:
        query.answer("Неизвестная кнопка.")
