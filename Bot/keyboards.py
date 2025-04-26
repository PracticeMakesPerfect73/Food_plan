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
        [InlineKeyboardButton("Другой рецепт", callback_data="get_recipe")],
        [InlineKeyboardButton("❤️", callback_data=f"like_{recipe_id}")],
        [InlineKeyboardButton("Показать детали", callback_data=f"details_{recipe_id}")],
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")],
    ]
    return InlineKeyboardMarkup(keyboard)


def recipe_details_keyboard(recipe_id):
    keyboard = [
        [InlineKeyboardButton("Другой рецепт", callback_data="get_recipe")],
        [InlineKeyboardButton("❤️", callback_data=f"like_{recipe_id}")],
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
    ]
    return InlineKeyboardMarkup(keyboard)


def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("Оформить подписку", callback_data="subscribe_placeholder")]
    ]
    return InlineKeyboardMarkup(keyboard)
