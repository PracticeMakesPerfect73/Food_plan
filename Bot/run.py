import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__))) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodBot.settings')
import django
django.setup()

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from handlers import start_command, get_recipe_action
from handlers import init_db, favorites_command, button_callback_handler
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TG_TOKEN')  # Токен бота Telegram


def main():
    """Запускает бота."""
    #  init_db() больше не потребуется, если управление пользователями и избранным также перенесено в Django
    init_db()  # Пока оставляем, если логика пользователей и избранного остается в SQLite

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

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