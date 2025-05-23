import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FoodBot.settings')
import django
django.setup()

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

from handlers import start_command, get_recipe_action, button_callback_handler

BOT_TOKEN = os.getenv('TG_TOKEN')


def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("recipe", get_recipe_action))
    dispatcher.add_handler(CallbackQueryHandler(button_callback_handler))

    print("Bot started polling...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()