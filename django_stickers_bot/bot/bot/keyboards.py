from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def see_sticker_set(sticker_set_name, sticker_file_unique_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Просмотреть весь набор",
                    callback_data=f"see_sticker_set:{sticker_set_name}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Просмотреть этот стикер",
                    callback_data=f"see_sticker:{sticker_file_unique_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "Удалить набор",
                    callback_data=f"delete_sticker_set:{sticker_set_name}",
                ),
            ],
        ],
    )


def add_sticker_set(name):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Да",
                    callback_data=f"add_sticker_set:{name}",
                ),
            ],
        ],
    )


def edit_sticker_text(sticker_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Изменить",
                    callback_data=f"edit_sticker_text:{sticker_id}",
                ),
            ],
        ],
    )


__all__ = ["see_sticker_set", "add_sticker_set", "edit_sticker_text"]
