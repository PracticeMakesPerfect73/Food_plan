import datetime
import keyboards
import os
import random
import sys

from django.db.models import Count
from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from FoodBot.models import Recipe, UserProfile

load_dotenv()
DAILY_FREE_LIMIT = int(os.getenv('DAILY_FREE_LIMIT', 3))

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def add_or_update_user(user_id):
    user, created = UserProfile.objects.get_or_create(user_id=user_id)
    today = datetime.date.today()

    if user.last_recipe_date != today:
        user.daily_recipes_count = 0
        user.last_recipe_date = today

    user.save()
    return user


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
    recipes = Recipe.objects.all()
    if not recipes.exists():
        return None
    return random.choice(recipes)


def get_random_favorite_recipe(user_id):
    liked_ids = get_liked_recipe_ids(user_id)
    if not liked_ids:
        return None
    recipes = Recipe.objects.filter(id__in=liked_ids)
    if not recipes.exists():
        return None
    return random.choice(recipes)


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

    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo_big.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as logo_file:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=logo_file
                )
        except Exception as e:
            print(f"Ошибка при отправке логотипа: {e}")

    update.message.reply_text(welcome_text, reply_markup=reply_markup)


def send_recipe(update, context, recipe):
    user_id = update.effective_user.id

    if not recipe:
        context.bot.send_message(chat_id=user_id, text="Нет доступных рецептов.")
        return

    caption = f"*{recipe.title}*"
    keyboard = [
        [InlineKeyboardButton("Другой рецепт", callback_data="get_recipe")],
        [InlineKeyboardButton("❤️", callback_data=f"like_{recipe.id}")],
        [InlineKeyboardButton("Показать детали", callback_data=f"show_details_{recipe.id}")],
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if recipe.image and recipe.image.path:
        try:
            with open(recipe.image.path, 'rb') as image_file:
                context.bot.send_photo(
                    chat_id=user_id,
                    photo=image_file,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            return
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")

    context.bot.send_message(
        chat_id=user_id,
        text=caption,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


def get_recipe_action(update, context, from_favorites=False):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    user = add_or_update_user(user_id)

    if not user.is_premium and user.daily_recipes_count >= DAILY_FREE_LIMIT:
        reply_markup = keyboards.subscribe_keyboard()
        context.bot.send_message(
            chat_id=user_id,
            text=f"Ваш дневной лимит ({DAILY_FREE_LIMIT} рецептов) исчерпан.\n"
                 f"Оформите подписку для безлимитного доступа!",
            reply_markup=reply_markup
        )
        return

    recipe = get_random_recipe()

    if recipe:
        user.daily_recipes_count += 1
        user.save()

        name = recipe.title
        photo = recipe.image

        caption = f"*{name}*"
        reply_markup = keyboards.recipe_keyboard(recipe.id)

        if photo and photo.path:
            try:
                with open(photo.path, 'rb') as image_file:
                    context.bot.send_photo(
                        chat_id=user_id,
                        photo=image_file,
                        caption=caption,
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


def show_recipe_details(update, context, recipe_id):
    user_id = update.effective_user.id
    try:
        recipe = Recipe.objects.get(id=recipe_id)
        details = f"*{recipe.title}*\n\nИнгредиенты и способ приготовления:\n\n{recipe.description}"

        keyboard = [
            [InlineKeyboardButton("Другой рецепт", callback_data="get_recipe")],
            [InlineKeyboardButton("❤️", callback_data=f"like_{recipe.id}")],
            [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(
            chat_id=user_id,
            text=details,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Recipe.DoesNotExist:
        context.bot.send_message(chat_id=user_id, text="Рецепт не найден.")


def get_recipe_by_id(recipe_id):
    try:
        return Recipe.objects.get(id=recipe_id)
    except Recipe.DoesNotExist:
        return None


def button_callback_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    if data == "get_recipe":
        get_recipe_action(update, context)
        return

    if data == "get_favorites":
        get_recipe_action(update, context, from_favorites=True)
        return
    
    elif data.startswith("details_"):
        try:
            recipe_id = int(data.split("_")[1])
            recipe = get_recipe_by_id(recipe_id)
            if not recipe:
                query.answer("Этот рецепт больше недоступен.")
                return
    
            caption = f"*{recipe.title}*\n\n{recipe.description}"
    
            reply_markup = keyboards.recipe_details_keyboard(recipe_id)
    
            context.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    
        except (ValueError, IndexError):
            query.answer("Ошибка при обработке запроса показа деталей.")

    elif data.startswith("like_"):
        try:
            recipe_id = int(data.split("_")[1])
            if not Recipe.objects.filter(id=recipe_id).exists():
                query.answer("Этот рецепт больше недоступен.")
                return
            added = add_liked_recipe(user_id, recipe_id)
            query.answer("Рецепт добавлен в избранное!" if added else "Этот рецепт уже в вашем избранном!")
        except (ValueError, IndexError):
            query.answer("Ошибка при обработке запроса лайка.")

    elif data.startswith("show_details_"):
        try:
            recipe_id = int(data.split("_")[2])
            show_recipe_details(update, context, recipe_id)
        except (ValueError, IndexError):
            query.answer("Ошибка при показе деталей.")

    elif data == "subscribe_placeholder":
        context.bot.send_message(chat_id=user_id, text="Раздел подписки в разработке!")

    else:
        query.answer("Неизвестная команда.")
