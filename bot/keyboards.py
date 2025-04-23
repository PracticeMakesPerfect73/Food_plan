from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard():
    keyboard = [
        [InlineKeyboardButton("Показать рецепт", callback_data="get_recipe")],
        [InlineKeyboardButton("Избранное", callback_data="get_favorites")],
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
    ]
    return InlineKeyboardMarkup(keyboard)


def recipe_keyboard(recipe_id):
    keyboard = [
        [InlineKeyboardButton("Список продуктов", callback_data=f"ingredients_{recipe_id}")],
        [InlineKeyboardButton("Поставить лайк", callback_data=f"like_{recipe_id}")],
        [InlineKeyboardButton("Показать еще рецепт", callback_data="get_recipe")],
        [InlineKeyboardButton("Назад в меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
    ]
    return InlineKeyboardMarkup(keyboard)
