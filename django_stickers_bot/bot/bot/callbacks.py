__all__ = (
    "AddSetCallback",
    "SetAction",
    "SetCallback",
    "StickerAction",
    "StickerCallback",
)

from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class SetAction(StrEnum):
    SHOW = "show"
    DELETE = "delete"


class StickerAction(StrEnum):
    SHOW = "show"
    EDIT = "edit"


class SetCallback(CallbackData, prefix="set"):
    action: SetAction
    set_id: int
    offset: int = 0


class StickerCallback(CallbackData, prefix="sticker"):
    action: StickerAction
    file_unique_id: str


class AddSetCallback(CallbackData, prefix="set_add"):
    pass
