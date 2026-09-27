__all__ = (
    "add_sticker_set",
    "edit_sticker_text",
    "more_stickers",
    "open_sticker_set",
    "see_sticker_set",
)

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.bot.callbacks import (
    AddSetCallback,
    SetAction,
    SetCallback,
    StickerAction,
    StickerCallback,
)


def see_sticker_set(
    set_id: int,
    sticker_file_unique_id: str,
) -> InlineKeyboardMarkup:
    show_set = SetCallback(action=SetAction.SHOW, set_id=set_id)
    show_sticker = StickerCallback(
        action=StickerAction.SHOW,
        file_unique_id=sticker_file_unique_id,
    )
    delete_set = SetCallback(action=SetAction.DELETE, set_id=set_id)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Просмотреть весь набор",
                    callback_data=show_set.pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Просмотреть этот стикер",
                    callback_data=show_sticker.pack(),
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Удалить набор",
                    callback_data=delete_set.pack(),
                ),
            ],
        ],
    )


def add_sticker_set() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да",
                    callback_data=AddSetCallback().pack(),
                ),
            ],
        ],
    )


def edit_sticker_text(sticker_file_unique_id: str) -> InlineKeyboardMarkup:
    edit = StickerCallback(
        action=StickerAction.EDIT,
        file_unique_id=sticker_file_unique_id,
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Изменить",
                    callback_data=edit.pack(),
                ),
            ],
        ],
    )


def open_sticker_set(set_id: int) -> InlineKeyboardMarkup:
    show = SetCallback(action=SetAction.SHOW, set_id=set_id)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Просмотреть набор",
                    callback_data=show.pack(),
                ),
            ],
        ],
    )


def more_stickers(set_id: int, offset: int) -> InlineKeyboardMarkup:
    more = SetCallback(action=SetAction.SHOW, set_id=set_id, offset=offset)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Показать ещё",
                    callback_data=more.pack(),
                ),
            ],
        ],
    )
