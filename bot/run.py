import os
import json
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Импортируем обработчики и функции БД/данных из handlers
from handlers import start_command, get_recipe_action
from handlers import init_db, favorites_command, button_callback_handler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TG_TOKEN')  # Токен бота Telegram 
RECIPES_FILE = "recipes.json"  # Имя файла с рецептами
IMAGES_FOLDER = "images"  # Имя папки с фотографиями


def load_recipes_from_json(file_path):
    """Загружает рецепты из JSON файла."""
    if not os.path.exists(file_path):
        print(
            f"Error: Recipes file not found: {file_path}.")
        return []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)
        return recipes_data
    except json.JSONDecodeError:
        print(f"Error: Error decoding JSON from {file_path}.")
        return []
    except Exception as e:
        print(f"Error: An error occurred while loading recipes from {file_path}: {e}")
        return []


def main():
    """Запускает бота."""
    init_db()  # Инициализируем базу данных (users и liked_recipes)

    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    recipes = load_recipes_from_json(RECIPES_FILE)
    dispatcher.bot_data['recipes'] = recipes  # Сохраняем список рецептов в данные бота через dispatcher

    # Регистрация обработчиков
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("recipe", get_recipe_action))
    dispatcher.add_handler(CommandHandler("favorites", favorites_command))

    # Обработчик Inline кнопок
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))

    # Запуск бота
    print("Bot started polling...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
