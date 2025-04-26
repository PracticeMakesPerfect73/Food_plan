import sys
import sqlite3
import datetime
import random
import os
from telegram import InlineKeyboardMarkup
import keyboards
from django.db.models import Count

sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
from FoodBot.models import Recipe, UserProfile

DB_NAME = "foodplan_mvp.db"
IMAGES_FOLDER = "images"
DAILY_FREE_LIMIT = 300


def add_or_update_user(user_id):
    user, created = UserProfile.objects.get_or_create(user_id=user_id)
    user.save()


def get_user_data(user_id):
    try:
        return UserProfile.objects.get(user_id=user_id)
    except UserProfile.DoesNotExist:
        return None


def add_liked_recipe(user_id, recipe_id):
    try:
        user = UserProfile.objects.get(user_id=user_id)
        recipe = Recipe.objects.get(id=recipe_id)
        user.favorite_recipes.add(recipe)
        return True
    except (UserProfile.DoesNotExist, Recipe.DoesNotExist):
        return False


def get_liked_recipe_ids(user_id):
    try:
        user = UserProfile.objects.get(user_id=user_id)
        return list(user.favorite_recipes.values_list('id', flat=True))
    except UserProfile.DoesNotExist:
        return []


def get_random_recipe():
    count = Recipe.objects.aggregate(count=Count('id'))['count']
    if count == 0:
        return None
    random_index = random.randint(0, count - 1)
    return Recipe.objects.all()[random_index]


def get_recipe_by_id(recipe_id):
    try:
        return Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return None
    except (ValueError, TypeError):
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

    recipe = get_random_recipe()

    if recipe:
        recipe_id = recipe.id
        name = recipe.title
        description = recipe.description
        photo = recipe.image

        caption = f"*{name}*\n\n{description}"
        reply_markup = keyboards.recipe_keyboard(recipe_id)

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
    add_or_update_user(user_id)
    liked_recipe_ids = get_liked_recipe_ids(user_id)

    if not liked_recipe_ids:
        response = "У вас пока нет избранных рецептов. Нажмите 'Поставить лайк' под понравившимся рецептом!"
    else:
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
            if not get_recipe_by_id(recipe_id):
                 query.answer("Этот рецепт больше недоступен.")
                 return

            added = add_liked_recipe(user_id, recipe_id)
            query.answer("Рецепт добавлен в избранное!" if added else "Этот рецепт уже в вашем избранном!")

        except (ValueError, IndexError):
            query.answer("Ошибка при обработке запроса лайка.")


    elif data == "subscribe_placeholder":
        context.bot.send_message(chat_id=user_id, text="Раздел подписки в разработке!")

    else:
        query.answer("Неизвестная кнопка.")
